import Gio from 'gi://Gio';
import Meta from 'gi://Meta';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

const BUS_NAME = 'org.magicmouse.Workspaces';
const OBJECT_PATH = '/org/magicmouse/Workspaces';
const IFACE_XML = `<node>
  <interface name="org.magicmouse.Workspaces">
    <method name="Switch">
      <arg type="s" name="direction" direction="in"/>
    </method>
    <method name="SwitchTo">
      <arg type="i" name="index" direction="in"/>
    </method>
    <method name="Overview"/>
    <method name="Ping">
      <arg type="b" name="ok" direction="out"/>
    </method>
    <method name="Status">
      <arg type="s" name="json" direction="out"/>
    </method>
  </interface>
</node>`;

function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
}

function workspaceStatus(backend) {
    const manager = global.workspace_manager;
    return JSON.stringify({
        backend,
        active: manager.get_active_workspace_index() + 1,
        count: manager.n_workspaces,
    });
}

function activateWorkspaceByIndex(indexZeroBased) {
    const manager = global.workspace_manager;
    const maxIndex = Math.max(0, manager.n_workspaces - 1);
    const targetIndex = clamp(indexZeroBased, 0, maxIndex);
    const workspace = manager.get_workspace_by_index(targetIndex);
    if (workspace)
        workspace.activate(global.get_current_time());
}

function switchRelative(direction) {
    const manager = global.workspace_manager;
    const activeIndex = manager.get_active_workspace_index();
    const normalized = String(direction).toLowerCase();

    // Magic Mouse vertical gestures: down means next workspace, up means previous.
    // left/right are accepted too for GNOME's horizontal workspace mental model.
    if (['next', 'down', 'right'].includes(normalized)) {
        activateWorkspaceByIndex(activeIndex + 1);
        return;
    }
    if (['prev', 'previous', 'up', 'left'].includes(normalized)) {
        activateWorkspaceByIndex(activeIndex - 1);
        return;
    }

    const motionMap = {
        'motion-up': Meta.MotionDirection.UP,
        'motion-down': Meta.MotionDirection.DOWN,
        'motion-left': Meta.MotionDirection.LEFT,
        'motion-right': Meta.MotionDirection.RIGHT,
    };

    if (motionMap[normalized] !== undefined) {
        const active = manager.get_active_workspace();
        const target = active.get_neighbor(motionMap[normalized]);
        if (target)
            target.activate(global.get_current_time());
    }
}

export default class MagicMouseWorkspacesExtension extends Extension {
    enable() {
        this._dbusObject = Gio.DBusExportedObject.wrapJSObject(IFACE_XML, this);
        this._dbusObject.export(Gio.DBus.session, OBJECT_PATH);
        this._busNameId = Gio.bus_own_name_on_connection(
            Gio.DBus.session,
            BUS_NAME,
            Gio.BusNameOwnerFlags.NONE,
            null,
            null
        );
    }

    disable() {
        if (this._dbusObject) {
            this._dbusObject.unexport();
            this._dbusObject = null;
        }
        if (this._busNameId) {
            Gio.bus_unown_name(this._busNameId);
            this._busNameId = 0;
        }
    }

    Switch(direction) { switchRelative(direction); }

    SwitchTo(index) {
        // DBus API is 1-based because humans say "workspace 1".
        activateWorkspaceByIndex(index - 1);
    }

    Overview() {
        Main.overview.toggle();
    }

    Ping() { return true; }

    Status() { return workspaceStatus('gnome-extension'); }
}
