// SPDX-License-Identifier: MIT
import QtQuick
import QtTest
import "." as Glass
Item {
    width: 300; height: 160
    Glass.PanelGlassSpinBox { id: spin; x: 20; y: 20; from: 0; to: 1000; value: 100; stepSize: 25 }
    SignalSpy { id: changes; target: spin; signalName: "valueModified" }
    TestCase {
        name: "GlassSpinBoxInteraction"
        when: windowShown
        function test_arrows_and_editing() {
            mouseClick(spin.up.indicator)
            compare(spin.value, 125)
            compare(changes.count, 1)
            mouseClick(spin.down.indicator)
            compare(spin.value, 100)
            spin.contentItem.forceActiveFocus()
            keyClick(Qt.Key_A, Qt.ControlModifier)
            keyClick(Qt.Key_1)
            keyClick(Qt.Key_7)
            keyClick(Qt.Key_5)
            keyClick(Qt.Key_Return)
            compare(spin.value, 175)
            verify(changes.count >= 3)
        }
    }
}
