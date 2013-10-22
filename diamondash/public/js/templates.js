this["JST"] = this["JST"] || {};

this["JST"]["diamondash/widgets/graph/legend.jst"] = function(obj) {
obj || (obj = {});
var __t, __p = '', __e = _.escape, __j = Array.prototype.join;
function print() { __p += __j.call(arguments, '') }
with (obj) {
__p += '<div class="row">\n  ';
 self.model.get('metrics').each(function(m) { ;
__p += '\n    <div class="legend-item col-md-6" data-metric-id="' +
((__t = ( m.get('id') )) == null ? '' : __t) +
'">\n      <span class="swatch"></span>\n      <span class="title">' +
((__t = ( m.get('title') )) == null ? '' : __t) +
'</span>\n      <span class="value">' +
((__t = ( self.format(x ? m.valueAt(x) : m.lastValue()) )) == null ? '' : __t) +
'</span>\n    </div>\n  ';
 }); ;
__p += '\n</div>\n';

}
return __p
};

this["JST"]["diamondash/widgets/lvalue/lvalue.jst"] = function(obj) {
obj || (obj = {});
var __t, __p = '', __e = _.escape;
with (obj) {
__p += '<h1 class="last"></h1>\n<div class="' +
((__t = ( change )) == null ? '' : __t) +
' change">\n  <span class="diff">' +
((__t = ( diff )) == null ? '' : __t) +
'</span>\n  <span class="percentage">(' +
((__t = ( percentage )) == null ? '' : __t) +
')</span>\n</div>\n<div class="time">\n  <span class="from">from ' +
((__t = ( from )) == null ? '' : __t) +
'</span>\n  <span class="to">to ' +
((__t = ( to )) == null ? '' : __t) +
'<span>\n</div>\n';

}
return __p
};

this["JST"]["diamondash/client/jst/dashboard.jst"] = function(obj) {
obj || (obj = {});
var __t, __p = '', __e = _.escape, __j = Array.prototype.join;
function print() { __p += __j.call(arguments, '') }
with (obj) {

 dashboard.model.get('rows').each(function(row) { ;
__p += '\n<div class="row">\n  ';
 row.get('widgets').each(function(widget) { ;
__p += '\n    <div\n     data-widget="' +
((__t = ( widget.id )) == null ? '' : __t) +
'"\n     class="widget col-md-' +
((__t = ( widget.get('width'))) == null ? '' : __t) +
'">\n      <div class="head"><h4>' +
((__t = ( widget.get('title') )) == null ? '' : __t) +
'</h4></div>\n      <div class="body"></div>\n    </div>\n  ';
 }); ;
__p += '\n</div>\n';
 }); ;
__p += '\n';

}
return __p
};