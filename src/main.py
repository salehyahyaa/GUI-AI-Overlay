import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSMenu,
    NSMenuItem,
    NSEventModifierFlagCommand,
)
from dotenv import load_dotenv
from Foundation import NSOperationQueue

from core.customKey import CustomKeyListener
from GUI.overlay import Overlay

_REPO_ROOT = _SRC.parent
load_dotenv(_REPO_ROOT / ".env")


def _install_clipboard_menu(app):
    """Minimal main menu so ⌘C / ⌘V / ⌘A resolve via responder chain (accessory apps need this)."""
    bar = NSMenu.alloc().init()
    app_item = NSMenuItem.alloc().init()
    bar.addItem_(app_item)
    app_menu = NSMenu.alloc().initWithTitle_("SnapPrompt")
    app_item.setSubmenu_(app_menu)
    quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit", "terminate:", "w")
    quit_item.setKeyEquivalentModifierMask_(NSEventModifierFlagCommand)
    app_menu.addItem_(quit_item)

    edit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Edit", None, "")
    edit_menu = NSMenu.alloc().initWithTitle_("Edit")
    edit_item.setSubmenu_(edit_menu)
    bar.addItem_(edit_item)
    for title, action, key in (
        ("Copy", "copy:", "c"),
        ("Paste", "paste:", "v"),
        ("Select All", "selectAll:", "a"),
    ):
        mi = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, action, key)
        mi.setKeyEquivalentModifierMask_(NSEventModifierFlagCommand)
        edit_menu.addItem_(mi)

    app.setMainMenu_(bar)


def main():
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    _install_clipboard_menu(app)

    overlay = Overlay.alloc().init()
    main_queue = NSOperationQueue.mainQueue()

    def schedule_toggle():
        main_queue.addOperationWithBlock_(lambda: overlay.toggle())

    listener = CustomKeyListener(schedule_toggle)
    listener.start()

    app.run()


if __name__ == "__main__":
    main()
