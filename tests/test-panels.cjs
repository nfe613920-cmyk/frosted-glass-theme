// SPDX-License-Identifier: MIT
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const script = fs.readFileSync(path.join(__dirname, '../layout/panels.js'), 'utf8');
const types = [...new Set(script.match(/(?:org\.kde\.plasma\.[a-z]+|local\.frosted\.dockseparator)/g))];
function run(available) {
  let removed = 0;
  const created = [];
  function Panel() { this.widgets = []; created.push(this); }
  Panel.prototype.addWidget = function(type) {
    const widget = {type, settings: {}, writeConfig(key, value) {this.settings[key] = value;}};
    this.widgets.push(widget);
    return widget;
  };
  const context = {Panel, knownWidgetTypes: available, panels: () => [{remove() {++removed;}}]};
  let error;
  try {vm.runInNewContext(script, context);} catch (e) {error = e;}
  return {removed, created, error};
}
const valid = run(types);
assert.equal(valid.error, undefined);
assert.equal(valid.removed, 1);
assert.equal(valid.created.length, 2);
assert.equal(valid.created[0].floating, true);
assert.equal(valid.created[0].opacity, 'translucent');
assert.equal(valid.created[1].lengthMode, 'fit');
assert.equal(valid.created[1].widgets[0].settings.launchers.length, 6);
const unavailable = run([]);
assert.ok(unavailable.error);
assert.equal(unavailable.removed, 0);
assert.equal(unavailable.created.length, 0);
console.log('Panel reconstruction and preflight tests passed.');
