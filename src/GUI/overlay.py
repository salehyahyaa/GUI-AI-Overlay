import time
import objc
from Foundation import NSObject, NSMakeRect, NSOperationQueue
from model.client import get_response
from AppKit import (
    NSApp,
    NSPanel,
    NSWindowStyleMaskTitled,
    NSWindowStyleMaskClosable,
    NSBackingStoreBuffered,
    NSPopUpMenuWindowLevel,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSWindowCollectionBehaviorMoveToActiveSpace,
    NSScreen,
    NSEvent,
    NSColor,
    NSMouseInRect,
    NSView,
    NSTextField,
    NSButton,
    NSScrollView,
    NSTextView,
    NSFont,
    NSBezelStyleRounded,
    NSControlSizeLarge,
    NSViewWidthSizable,
    NSViewHeightSizable,
    NSViewMinXMargin,
    NSEventModifierFlagCommand,
)


class KeyablePanel(NSPanel):
    """Panel must route ⌘C / ⌘V / ⌘X / ⌘A — accessory apps often lack working Edit menu routing."""

    def canBecomeKeyWindow(self):
        return True

    def performKeyEquivalent_(self, event):
        if event.modifierFlags() & NSEventModifierFlagCommand:
            chars = event.charactersIgnoringModifiers()
            if chars and len(chars) > 0:
                c = chars[0].lower()
                action = {"c": "copy:", "v": "paste:", "x": "cut:", "a": "selectAll:"}.get(c)
                if action is not None and NSApp.sendAction_to_from_(action, None, None):
                    return True
        return objc.super(KeyablePanel, self).performKeyEquivalent_(event)


class Overlay(NSObject):
    def init(self):                                                                              # PyObjC designated initializer pattern
        self = objc.super(Overlay, self).init()                                                  # Call NSObject init correctly via objc.super
        if self is None:                                                                         # Defensive: init failed
            return None                                                                          # Propagate init failure to caller
        style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable                              # Title bar + close button chrome flags
        self.window = KeyablePanel.alloc().initWithContentRect_styleMask_backing_defer_(         # Create the floating panel window instance
            NSMakeRect(0, 0, 480, 360),                                                          # Initial rect (re-centered when shown)
            style,                                                                               # Style mask bitmask for decorations/behavior
            NSBackingStoreBuffered,                                                              # Buffered backing store for smoother drawing
            False,                                                                               # Defer creation flag (False = create now)
        )                                                                                        # End panel initializer call
        self.window.setFloatingPanel_(True)                                                      # Floating utility-style panel behavior
        self.window.setWorksWhenModal_(True)                                                     # Still usable when other UI is modal-ish
        self.window.setLevel_(NSPopUpMenuWindowLevel)                                            # Raise above normal document windows (overlay feel)
        self.window.setCollectionBehavior_(                                                      # Spaces: move with active Space (no “clone on every desktop”)
            NSWindowCollectionBehaviorMoveToActiveSpace
            | NSWindowCollectionBehaviorFullScreenAuxiliary
        )
        self.window.setReleasedWhenClosed_(False)                                                # Don’t auto-release ObjC object on close
        self.window.setHidesOnDeactivate_(False)                                                 # Don’t auto-hide when app loses active status
        self.window.setOpaque_(True)                                                             # Opaque background (simpler compositing)
        self.window.setBackgroundColor_(NSColor.windowBackgroundColor())                         # Standard macOS window background color
        self.window.setTitle_("Open Search")                                                     # Titlebar text for the overlay window
        self._toggle_debounce_s = 0.22                                                           # Ignore rapid duplicate hotkey toggles
        self._last_toggle_mono = 0.0                                                             # Last toggle time (monotonic clock)
        self._worker_queue = NSOperationQueue.alloc().init()                                     # Background queue for network/OpenAI work
        self._worker_queue.setMaxConcurrentOperationCount_(1)                                    # Serialize API calls (avoid overlap)
        self._main_queue = NSOperationQueue.mainQueue()                                          # Main/UI queue for AppKit-only updates
        content = self.window.contentView()                                                      # Default content view AppKit provides
        bounds = content.bounds()                                                                # Content area size in window coordinates
        w, h = bounds.size.width, bounds.size.height                                             # Extract width/height for layout math
        root = NSView.alloc().initWithFrame_(bounds)                                             # Root view filling the entire content area
        root.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)                      # Grow/shrink with window width and height
        scroll = NSScrollView.alloc().initWithFrame_(                                            # Scroll container for long model output
            NSMakeRect(8, 48, w - 16, h - 56)                                                    # Inset rect leaving bottom row for input/send
        )                                                                                        # End scroll view frame
        scroll.setHasVerticalScroller_(True)                                                     # Vertical scrollbar when text overflows
        scroll.setAutohidesScrollers_(True)                                                      # Hide scrollers until scrolling
        scroll.setBorderType_(1)                                                                 # Bezel border around scroll area (NSBezelBorder)
        scroll.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)                    # Resize scroll area with the window
        self.output_view = NSTextView.alloc().initWithFrame_(scroll.bounds())                    # Multiline output text view inside scroll view
        self.output_view.setMinSize_(scroll.bounds().size)                                       # Minimum size matches viewport for layout stability
        self.output_view.setMaxSize_((1e7, 1e7))                                                 # Large max size so vertical growth can scroll
        self.output_view.setVerticallyResizable_(True)                                           # Allow growing vertically as text grows
        self.output_view.setHorizontallyResizable_(False)                                        # Keep width pinned (wrap within scroll width)
        self.output_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)          # Track scroll view bounds changes
        self.output_view.setEditable_(False)                                                     # Output is read-only
        self.output_view.setSelectable_(True)                                                    # Allow select + ⌘C copy from answers
        self.output_view.setRichText_(False)                                                      # Plain text: predictable copy/paste behavior
        self.output_view.setImportsGraphics_(False)                                               # Don’t treat drops as images in read-only view
        self.output_view.setFont_(NSFont.systemFontOfSize_(13))                                  # Readable default system font size
        self.output_view.setString_("")                                                          # Start empty before first response
        scroll.setDocumentView_(self.output_view)                                                # Attach text view as scroll view document
        self.input_field = NSTextField.alloc().initWithFrame_(NSMakeRect(8, 8, w - 100, 28))     # Single-line prompt input near bottom
        self.input_field.setPlaceholderString_("Ask something…")                                 # Hint text when field is empty
        self.input_field.setFont_(NSFont.systemFontOfSize_(13))                                  # Match output font size for consistency
        self.input_field.setEditable_(True)                                                       # Typing + ⌘V paste into prompt
        self.input_field.setSelectable_(True)                                                   # ⌘A / ⌘C from prompt field
        self.input_field.setAutoresizingMask_(NSViewWidthSizable)                                # Stretch width; Send stays fixed width
        self.input_field.setUsesSingleLineMode_(True)                                            # Return sends instead of inserting newline
        self.input_field.setDelegate_(self)                                                      # control_textView_doCommandBySelector_ for Return
        self.send_button = NSButton.alloc().initWithFrame_(NSMakeRect(w - 84, 4, 76, 32))        # Push button near bottom-right corner
        self.send_button.setTitle_("Send")                                                       # Label for submitting the prompt
        self.send_button.setBezelStyle_(NSBezelStyleRounded)                                    # Rounded push button appearance
        self.send_button.setControlSize_(NSControlSizeLarge)                                     # Slightly larger control hit target
        self.send_button.setAutoresizingMask_(NSViewMinXMargin)                                 # Keep pinned to trailing edge when window widens
        self.send_button.setTarget_(self)                                                        # Route actions to this Overlay instance
        self.send_button.setAction_("send:")                                                     # ObjC `send:` maps to Python `send_`
        root.addSubview_(scroll)                                                                # Add scroll/output into root view
        root.addSubview_(self.input_field)                                                       # Add prompt field into root view
        root.addSubview_(self.send_button)                                                      # Add send button into root view
        self.window.setContentView_(root)                                                        # Install composed UI as panel content
        self.window.setInitialFirstResponder_(self.input_field)                                  # Focus prompt when window becomes key
        self.window.setDefaultButtonCell_(self.send_button.cell())                               # Enter triggers default action when field allows
        return self                                                                              # Return initialized Overlay controller

    def control_textView_doCommandBySelector_(self, control, textView, commandSelector):
        if control is not self.input_field:
            return False
        if isinstance(commandSelector, bytes):
            name = commandSelector.decode("utf-8", "replace")
        elif isinstance(commandSelector, str):
            name = commandSelector
        else:
            name = getattr(commandSelector, "__name__", None) or str(commandSelector)
        if name == "insertNewline:" or name.rstrip(":") == "insertNewline":
            self.send_(self.send_button)
            return True
        return False

    def _focus_prompt(self):
        self.window.makeFirstResponder_(self.input_field)

    def _set_output(self, text):                                                                 # Central helper to replace output text
        self.output_view.setString_(text)                                                        # Non-streaming: replace whole output string
    
    
    def send_(self, sender):                                                                     # Button action (`send:` → `send_` in PyObjC)
        prompt = self.input_field.stringValue().strip()                                          # Read prompt; strip whitespace
        if not prompt:                                                                           # Guard empty submits
            return                                                                                # No API call for empty string
        self._set_output("…")                                                                     # Small loading indicator before response
        self.send_button.setEnabled_(False)                                                      # Prevent double-submit while in flight
       
       
        def work():                                                                              # Runs on background queue
            try:                                                                                  # Keep failures from crashing UI thread
                text = get_response(prompt)                                                       # Blocking OpenAI call (off main thread)
            except Exception as e:                                                               # Network/SDK/config errors land here
                text = f"Error: {e}"                                                              # User-visible error string
            def apply():                                                                          # Runs on main queue for UI mutation
                self._set_output(text)                                                            # Show model output or error in UI
                self.send_button.setEnabled_(True)                                               # Re-enable submit after completion
                self._focus_prompt()                                                              # Ready for next prompt without clicking

            self._main_queue.addOperationWithBlock_(apply)                                        # AppKit updates must happen on main thread
        self._worker_queue.addOperationWithBlock_(work)                                          # Don’t block the main event loop on HTTP
   
   
    def _frame_centered_under_cursor(self):                                                      # Center panel on screen containing mouse
        mouse = NSEvent.mouseLocation()                                                          # Mouse location in screen coordinates
        screen = None                                                                            # Matched NSScreen (if any)
        for s in NSScreen.screens():                                                             # Scan each connected display
            if NSMouseInRect(mouse, s.frame(), False):                                           # Mouse inside this screen’s frame?
                screen = s                                                                       # Remember this screen
                break                                                                            # Stop after first match
        if screen is None:                                                                       # If no match (edge case)
            screen = NSScreen.mainScreen()                                                       # Fall back to primary display
        sf = screen.frame()                                                                      # Chosen display’s full frame
        wf = self.window.frame()                                                                 # Current window size (width/height kept)
        x = sf.origin.x + (sf.size.width - wf.size.width) / 2.0                                  # Center X within display frame
        y = sf.origin.y + (sf.size.height - wf.size.height) / 2.0                                # Center Y within display frame
        return NSMakeRect(x, y, wf.size.width, wf.size.height)                                   # New origin; same window dimensions
    
    
    def toggle(self):                                                                            # Hotkey: show/hide overlay
        now = time.monotonic()
        if now - self._last_toggle_mono < self._toggle_debounce_s:
            return
        self._last_toggle_mono = now
        if self.window.isVisible():
            self.window.orderOut_(None)
        else:
            self.window.setFrame_display_(self._frame_centered_under_cursor(), True)
            self.window.makeKeyAndOrderFront_(None)
            NSApp.activateIgnoringOtherApps_(True)
            self._main_queue.addOperationWithBlock_(self._focus_prompt)
