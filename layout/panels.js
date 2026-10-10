// SPDX-License-Identifier: MIT
// Explicit opt-in: replaces all panels. Installer saves their config first.
var required = ["org.kde.plasma.kickoff", "org.kde.plasma.pager", "org.kde.plasma.panelspacer", "org.kde.plasma.marginsseparator", "org.kde.plasma.systemtray", "org.kde.plasma.digitalclock", "org.kde.plasma.showdesktop", "org.kde.plasma.icontasks", "local.frosted.dockseparator"];
for (var i = 0; i < required.length; ++i) {
    if (knownWidgetTypes.indexOf(required[i]) < 0) {
        throw new Error("Widget unavailable: " + required[i] + ". Log out and back in after installing the theme, then retry.");
    }
}
var previous = panels();
for (var i = 0; i < previous.length; ++i) previous[i].remove();

var top = new Panel;
top.location = "top";
top.height = 46;
top.lengthMode = "fill";
top.alignment = "center";
top.offset = 0;
top.floating = true;
top.opacity = "translucent";
top.hiding = "none";
var kickoff = top.addWidget("org.kde.plasma.kickoff");
kickoff.currentConfigGroup = [];
kickoff.writeConfig("popupHeight", 529);
kickoff.writeConfig("popupWidth", 621);
top.addWidget("org.kde.plasma.pager");
top.addWidget("org.kde.plasma.panelspacer");
top.addWidget("org.kde.plasma.marginsseparator");
top.addWidget("org.kde.plasma.systemtray");
top.addWidget("org.kde.plasma.digitalclock");
top.addWidget("org.kde.plasma.showdesktop");

var dock = new Panel;
dock.location = "bottom";
dock.height = 72;
dock.lengthMode = "fit";
dock.alignment = "center";
dock.offset = 0;
dock.floating = true;
dock.opacity = "translucent";
dock.hiding = "dodgewindows";
var tasks = dock.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", ["applications:systemsettings.desktop", "applications:org.kde.dolphin.desktop", "applications:org.kde.konsole.desktop", "applications:google-chrome.desktop", "applications:codex-desktop.desktop", "applications:antigravity.desktop"]);
dock.addWidget("local.frosted.dockseparator");
