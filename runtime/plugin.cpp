// SPDX-License-Identifier: MIT
#include <QGenericPlugin>
#include <unistd.h>
#include <QApplication>
#include <QAbstractScrollArea>
#include <QHeaderView>
#include <QScrollBar>
#include <QDir>
#include <QEvent>
#include <QPainter>
#include <QPainterPath>
#include <QMenu>
#include <QQuickWindow>
#include <QQuickWidget>
#include <QQuickItem>
#include <QQmlEngine>
#include <QQmlProperty>
#include <QTimer>
#include <QVariant>
#include <KColorScheme>
#include <KSharedConfig>
#include <KWindowEffects>
#include <Kirigami/Platform/PlatformTheme>

using Theme = Kirigami::Platform::PlatformTheme;

class GlassRuntime : public QObject {
    const bool popupsOnly = qEnvironmentVariableIsSet("PANEL_GLASS_POPUPS_ONLY");
    bool widgetsReady = false;
    void prepareMenu(QMenu *menu) {
        if (menu->property("_panelGlassMenu").toBool()) return;
        menu->setProperty("_panelGlassMenu", true);
        menu->setAttribute(Qt::WA_TranslucentBackground);
        menu->setAttribute(Qt::WA_OpaquePaintEvent, false);
        menu->setAutoFillBackground(false);
        // A local stylesheet also wins over the application's transparent QFrame
        // rule. Leave native action layout, icons, checks and shortcuts intact.
        menu->setStyleSheet(menu->styleSheet() + QStringLiteral(
            "QMenu { background: rgba(27,43,55,145); border: none; border-radius: 14px; padding: 6px; }"
            "QMenu::item:selected { background: rgba(73,183,223,45); border-radius: 4px; }"
            "QMenu::separator { background: rgba(255,255,255,30); height: 1px; margin: 5px 6px; }"));
    }
    void blurMenu(QMenu *menu) {
        if (!menu->windowHandle()) return;
        QPainterPath path;
        path.addRoundedRect(QRectF(menu->rect()), 14, 14);
        // Blur only the rounded surface, not the transparent corner pixels.
        KWindowEffects::enableBlurBehind(menu->windowHandle(), true,
            QRegion(path.toFillPolygon().toPolygon()));
    }
    bool pending = false;
    QPalette glassPalette;
    void recolorItems() {
        pending = false;
        for (auto *window : QGuiApplication::allWindows()) {
            auto *quick = qobject_cast<QQuickWindow *>(window);
            if (!quick) continue;
            // Incubated delegates need not share their visual parent's QObject
            // ownership; walk the visual tree so asynchronously loaded cards work.
            QList<QQuickItem *> items{quick->contentItem()};
            for (qsizetype i = 0; i < items.size(); ++i) items.append(items.at(i)->childItems());
            for (auto *item : items) {
                if (!item->property("_panelGlassChildren").toBool()) {
                    item->setProperty("_panelGlassChildren", true);
                    connect(item, &QQuickItem::childrenChanged, this, [this] { schedule(); });
                }
                // Kirigami cards contain an extra rectangle with a hard-coded
                // 60% shadow opacity; tint it separately from their live feedback.
                if (QByteArray(item->metaObject()->className()).startsWith("DefaultCardBackground_QMLTYPE_")) {
                    QQmlProperty(item, QStringLiteral("defaultColor")).write(QColor(255,255,255,12));
                    QQmlProperty(item, QStringLiteral("hoverColor")).write(QColor(73,183,223,45));
                    QQmlProperty(item, QStringLiteral("pressedColor")).write(QColor(73,183,223,70));
                    QQmlProperty(item, QStringLiteral("borderColor")).write(QColor(255,255,255,40));
                    for (auto *child : item->childItems()) {
                        if (QByteArray(child->metaObject()->className()) == "QQuickRectangle")
                            QQmlProperty(child, QStringLiteral("color")).write(QColor(255,255,255,8));
                    }
                }
                auto *theme = qobject_cast<Theme *>(qmlAttachedPropertiesObject<Theme>(item, false));
                if (!theme) continue;
                updateTheme(theme);
                if (!theme->property("_panelGlassConnected").toBool()) {
                    theme->setProperty("_panelGlassConnected", true);
                    connect(theme, &Theme::colorSetChanged, this, [this, theme] { updateTheme(theme); });
                }
            }
        }
    }
    void updateTheme(Theme *theme) {
        if (theme->colorSet() == Theme::Selection) return;
        const auto color = theme->colorSet() == Theme::Button ? QColor(255,255,255,12)
            : theme->colorSet() == Theme::Tooltip ? QColor(27,43,55,145) : QColor(Qt::transparent);
        theme->setCustomBackgroundColor(color);
        theme->setCustomAlternateBackgroundColor(QColor(255,255,255,10));
    }
    void schedule() {
        if (popupsOnly || pending) return;
        pending = true;
        QTimer::singleShot(0, this, [this] { initWidgets(); recolorItems(); });
    }
    void initWidgets() {
        if (widgetsReady || !qobject_cast<QApplication *>(qGuiApp)) return;
        widgetsReady = true;
        QApplication::setPalette(glassPalette);
        qApp->setStyleSheet(QStringLiteral(
            "QWidget[panelGlassWindow=\"true\"] { background: transparent; border: none; }"
            "QFrame, QStackedWidget, QAbstractScrollArea, QAbstractItemView, QQuickWidget { background: transparent; border: none; }"
            "QToolBar, QMenuBar, QStatusBar { background: transparent; border: none; }"
            "QHeaderView::section { background: rgba(255,255,255,12); border: none; padding: 4px; }"
            "QHeaderView::section:hover { background: rgba(255,255,255,28); }"
            "QPushButton { background: rgba(255,255,255,12); border: 1px solid rgba(255,255,255,40); border-radius: 6px; padding: 5px 10px; }"
            "QPushButton:hover { background: rgba(255,255,255,28); }"
            "QPushButton:pressed { background: rgba(73,183,223,45); }"
            "QPushButton:focus { border-color: rgba(73,183,223,180); }"
            "QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: rgba(255,255,255,12); border: 1px solid rgba(255,255,255,40); border-radius: 4px; padding: 4px; }"
            "QMenu { background: rgba(27,43,55,145); border: none; border-radius: 14px; padding: 6px; }"
            "QMenu::item:selected { background: rgba(73,183,223,45); border-radius: 4px; }"
            "QScrollBar { background: transparent; width: 10px; height: 10px; }"
            "QScrollBar::handle { background: rgba(255,255,255,60); border-radius: 4px; min-height: 20px; min-width: 20px; }"
            "QScrollBar::add-line, QScrollBar::sub-line { width: 0px; height: 0px; }"
            "QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }"));
    }
public:
    GlassRuntime() : QObject(nullptr) {
        if (!popupsOnly) {
            const QString scheme = qEnvironmentVariable("PANEL_GLASS_SCHEME", QDir::homePath() + QStringLiteral("/.local/opt/panelglass-runtime/PanelGlassTransparent.colors"));
            qGuiApp->setProperty("KDE_COLOR_SCHEME_PATH", scheme);
            glassPalette = KColorScheme::createApplicationPalette(KSharedConfig::openConfig(scheme));
            QGuiApplication::setPalette(glassPalette);
            QQuickWindow::setDefaultAlphaBuffer(true);
        }
        qGuiApp->installEventFilter(this);
    }
    bool eventFilter(QObject *object, QEvent *event) override {
        if (auto *menu = qobject_cast<QMenu *>(object)) {
            if (event->type() == QEvent::Polish || event->type() == QEvent::Show)
                prepareMenu(menu);
            if (event->type() == QEvent::Show || event->type() == QEvent::Resize)
                blurMenu(menu);
            // Keep Qt's native menu event handling and item painting.
            return QObject::eventFilter(object, event);
        }
        if (popupsOnly) return QObject::eventFilter(object, event);
        if (event->type() == QEvent::ChildAdded || event->type() == QEvent::Show) schedule();
        if (auto *widget = qobject_cast<QWidget *>(object)) {
            if (event->type() == QEvent::ChildAdded || event->type() == QEvent::Polish) {
                if (widget->isWindow()) {
                    widget->setProperty("panelGlassWindow", true);
                    widget->setAttribute(Qt::WA_StyledBackground);
                    widget->setAttribute(Qt::WA_TranslucentBackground);
                    widget->setAttribute(Qt::WA_OpaquePaintEvent, false);
                    widget->setAutoFillBackground(false);
                }
                if (auto *area = qobject_cast<QAbstractScrollArea *>(widget)) {
                    if (auto *viewport = area->viewport()) {
                        viewport->setAutoFillBackground(false);
                        viewport->setAttribute(Qt::WA_OpaquePaintEvent, false);
                    }
                }
                if (qobject_cast<QHeaderView *>(widget) || qobject_cast<QScrollBar *>(widget)) {
                    widget->setAutoFillBackground(false);
                    widget->setAttribute(Qt::WA_OpaquePaintEvent, false);
                }
                if (auto *quick = qobject_cast<QQuickWidget *>(widget)) {
                    quick->setClearColor(Qt::transparent);
                    quick->setAttribute(Qt::WA_OpaquePaintEvent, false);
                    quick->setAttribute(Qt::WA_AlwaysStackOnTop);
                    quick->setAutoFillBackground(false);
                }
            }
            // Some child widgets polish while QDockWidget is still constructing.
            // Defer application-wide style setup until the event loop is running.
            if (event->type() == QEvent::Polish) schedule();
            if (event->type() == QEvent::Show && widget->isWindow())
                KWindowEffects::enableBlurBehind(widget->windowHandle(), true);
            if (event->type() == QEvent::Paint && widget->isWindow()
                && widget->windowType() != Qt::Popup && widget->windowType() != Qt::ToolTip) {
                QPainter painter(widget);
                painter.setCompositionMode(QPainter::CompositionMode_Source);
                painter.fillRect(widget->rect(), QColor(27,43,55,145));
            }
            // KTitleWidget's text is in child labels; its own paint only adds a separator.
            if (event->type() == QEvent::Paint && widget->inherits("KTitleWidget")) return true;
        }
        if (auto *window = qobject_cast<QQuickWindow *>(object)) {
            if (event->type() == QEvent::Show && !window->inherits("QQuickWidgetOffscreenWindow") && !qobject_cast<QWidget *>(window->parent()) && window->type() != Qt::Popup) {
                // QRhi clears need premultiplied channels, unlike QPainter fillRect.
                const QColor clear(15,24,31,145);
                window->setColor(clear);
                if (!window->property("_panelGlassClear").toBool()) {
                    window->setProperty("_panelGlassClear", true);
                    connect(window, &QQuickWindow::colorChanged, this, [window, clear] {
                        if (window->color() != clear) window->setColor(clear);
                    });
                }
                KWindowEffects::enableBlurBehind(window, true);
            }
        }
        return QObject::eventFilter(object, event);
    }
};

class GlassPlugin : public QGenericPlugin {
    Q_OBJECT
    Q_PLUGIN_METADATA(IID QGenericPluginFactoryInterface_iid FILE "plugin.json")
public:
    QObject *create(const QString &key, const QString &) override {
        if (key.compare(QStringLiteral("panelglass"), Qt::CaseInsensitive) != 0) return nullptr;
        // Subprocesses such as Info Center's offscreen GPU probes keep their native
        // environment and must not receive window styling intended for their parent.
        char executable[4096];
        const auto length = readlink("/proc/self/exe", executable, sizeof(executable));
        const auto host = qgetenv("PANEL_GLASS_HOST");
        if (host.isEmpty() || length < 0 || host != QByteArray(executable, length)) return new QObject;
        return new GlassRuntime;
    }
};
#include "plugin.moc"
