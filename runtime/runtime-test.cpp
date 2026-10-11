// SPDX-License-Identifier: MIT
#include <QApplication>
#include <QMainWindow>
#include <QMenu>
#include <QDockWidget>
#include <QTreeWidget>
#include <QPushButton>
#include <QLineEdit>
#include <QSpinBox>
#include <QVBoxLayout>
#include <QQuickView>
#include <QQuickItem>
#include <QQmlComponent>
#include <QFileInfo>
#include <QtTest>

class RuntimeTest : public QObject {
    Q_OBJECT
private slots:
    void roundedMenusKeepNativeActions() {
        QWidget parent;
        const auto originalPalette = parent.palette();
        QMenu menu(&parent);
        auto *checked = menu.addAction("Keep checked action");
        checked->setCheckable(true);
        auto *disabled = menu.addAction("Keep disabled action");
        disabled->setEnabled(false);
        menu.addSeparator();
        auto *submenu = menu.addMenu("Keep submenu");
        auto *nested = submenu->addAction("Keep nested action");
        menu.popup(QPoint(100,100)); QTest::qWait(80);
        QVERIFY(menu.testAttribute(Qt::WA_TranslucentBackground));
        auto first = menu.grab().toImage();
        QCOMPARE(first.pixelColor(0,0).alpha(), 0);
        const auto base = first.pixelColor(menu.width()/2, 2);
        QVERIFY2(base.alpha() >= 140 && base.alpha() <= 150, qPrintable(QString::number(base.alpha())));
        menu.update(); QTest::qWait(20);
        QCOMPARE(menu.grab().toImage().pixelColor(menu.width()/2, 2), base);
        QSignalSpy triggered(checked, &QAction::triggered);
        QTest::keyClick(&menu, Qt::Key_Down);
        QTest::keyClick(&menu, Qt::Key_Return);
        QCOMPARE(triggered.size(), 1); QVERIFY(checked->isChecked());
        QVERIFY(!disabled->isEnabled());
        menu.popup(QPoint(100,100)); QTest::qWait(20);
        menu.setActiveAction(submenu->menuAction());
        QTest::keyClick(&menu, Qt::Key_Right); QTest::qWait(40);
        QVERIFY(submenu->isVisible());
        QVERIFY(submenu->testAttribute(Qt::WA_TranslucentBackground));
        QCOMPARE(submenu->grab().toImage().pixelColor(0,0).alpha(), 0);
        QSignalSpy nestedTriggered(nested, &QAction::triggered);
        QTest::keyClick(submenu, Qt::Key_Down); QTest::keyClick(submenu, Qt::Key_Return);
        QCOMPARE(nestedTriggered.size(), 1);
        if (qEnvironmentVariableIsSet("PANEL_GLASS_POPUPS_ONLY")) {
            QVERIFY(!parent.testAttribute(Qt::WA_TranslucentBackground));
            QCOMPARE(parent.palette(), originalPalette);
        }
    }
    void widgetInputAndSingleBackground() {
        if (qEnvironmentVariableIsSet("PANEL_GLASS_POPUPS_ONLY")) QSKIP("Private apps paint their own main windows");
        QMainWindow window;
        auto *dock = new QDockWidget("Keep dock controls", &window);
        dock->setWidget(new QLineEdit(dock));
        window.addDockWidget(Qt::LeftDockWidgetArea, dock);
        auto *central = new QWidget(&window);
        auto *layout = new QVBoxLayout(central);
        auto *button = new QPushButton("Keep this button", central);
        auto *edit = new QLineEdit(central);
        auto *spin = new QSpinBox(central);
        auto *table = new QTreeWidget(central);
        table->setHeaderLabel("Keep table header");
        table->addTopLevelItem(new QTreeWidgetItem(QStringList{"Keep data"}));
        layout->addWidget(button); layout->addWidget(edit); layout->addWidget(spin); layout->addWidget(table);
        window.setCentralWidget(central); window.resize(400,300); window.show();
        QTest::qWait(100);
        QVERIFY(window.testAttribute(Qt::WA_TranslucentBackground));
        QSignalSpy clicked(button, &QPushButton::clicked);
        QTest::mouseClick(button, Qt::LeftButton); QCOMPARE(clicked.size(), 1);
        QTest::keyClicks(edit, "native keyboard input"); QCOMPARE(edit->text(), QString("native keyboard input"));
        spin->setFocus(); QTest::keyClick(spin, Qt::Key_Up); QCOMPARE(spin->value(), 1);
        auto first = window.grab().toImage().pixelColor(395,295);
        QVERIFY2(first.alpha() >= 135 && first.alpha() <= 155, qPrintable(QString::number(first.alpha())));
        window.update(); QTest::qWait(30);
        auto second = window.grab().toImage().pixelColor(395,295);
        QCOMPARE(first, second);
    }
    void asynchronouslyAddedCardKeepsFeedbackAndContent() {
        if (qEnvironmentVariableIsSet("PANEL_GLASS_POPUPS_ONLY")) QSKIP("Private apps style their own Qt Quick content");
        QQuickView view; view.resize(300,200); view.show();
        QQmlComponent component(view.engine());
        component.setData("import QtQuick\nimport org.kde.kirigami as K\nK.AbstractCard { width: 200; height: 100; hoverEnabled: true; showClickFeedback: true; contentItem: Text { text: 'Keep card content' } }", QUrl());
        QTRY_VERIFY_WITH_TIMEOUT(component.status() != QQmlComponent::Loading, 5000);
        QVERIFY2(component.isReady(), qPrintable(component.errorString()));
        auto *card = qobject_cast<QQuickItem *>(component.create()); QVERIFY(card);
        // Deliberately no QObject parent: Discover and monitor use incubated items.
        card->setProperty("hoverEnabled", false);
        card->setParentItem(view.contentItem());
        QTest::mouseMove(&view, QPoint(290,190));
        QTest::qWait(100);
        auto *background = card->property("background").value<QQuickItem *>(); QVERIFY(background);
        QCOMPARE(background->property("defaultColor").value<QColor>().alpha(), 12);
        QCOMPARE(background->property("color").value<QColor>().alpha(), 12);
        card->setProperty("highlighted", true); QTest::qWait(20);
        QCOMPARE(background->property("color").value<QColor>().alpha(), 70);
        QCOMPARE(card->property("contentItem").value<QQuickItem *>()->property("text").toString(), QString("Keep card content"));
        delete card;
    }
};
int main(int argc, char **argv) {
    qputenv("PANEL_GLASS_HOST", QFileInfo(QString::fromLocal8Bit(argv[0])).canonicalFilePath().toLocal8Bit());
    QApplication app(argc, argv); RuntimeTest test; return QTest::qExec(&test, argc, argv);
}
#include "runtime-test.moc"
