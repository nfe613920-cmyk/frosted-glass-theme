import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore

PlasmoidItem {
    id: root
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation
    Layout.minimumWidth: 0
    Layout.preferredWidth: 0
    Layout.maximumWidth: 0
    property var taskList: null
    property var firstTask: null

    function findTasks(item, depth) {
        if (!item || depth > 20) return null;
        if (item.iconsOnly === true && item.taskList !== undefined) return item.taskList;
        for (let child of item.children || []) {
            let found = findTasks(child, depth + 1);
            if (found) return found;
        }
        return null;
    }
    Timer {
        interval: 500
        running: true
        repeat: true
        onTriggered: {
            if (!root.taskList && root.Window.window)
                root.taskList = root.findTasks(root.Window.window.contentItem, 0);
            if (!root.taskList) return;
            let first = null;
            for (let item of root.taskList.children) {
                if (item.index === 0 && item.model !== undefined) { first = item; break; }
            }
            root.firstTask = first;
        }
    }
    Rectangle {
        parent: root.taskList ? root.taskList.parent : root
        visible: root.firstTask !== null
        z: 100
        x: root.firstTask ? root.taskList.x + root.firstTask.x + root.firstTask.width - width / 2 : 0
        y: parent ? (parent.height - height) / 2 : 0
        width: 1
        height: parent ? Math.min(30, parent.height * 0.6) : 0
        color: "#70ffffff"
    }
    fullRepresentation: Item {
        implicitWidth: 0
        implicitHeight: 48
        Layout.minimumWidth: 0
        Layout.preferredWidth: 0
        Layout.maximumWidth: 0
    }
}
