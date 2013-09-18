this["JST"] = this["JST"] || {};

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

this["JST"]["diamondash/widgets/graph/legend.jst"] = function(obj) {
obj || (obj = {});
var __t, __p = '', __e = _.escape, __j = Array.prototype.join;
function print() { __p += __j.call(arguments, '') }
with (obj) {

 self.model.get('metrics').each(function(m) { ;
__p += '\n<li class="legend-item" data-name="' +
((__t = ( m.get('name') )) == null ? '' : __t) +
'">\n  <span class="swatch"></span>\n  <span class="title">' +
((__t = ( m.get('title') )) == null ? '' : __t) +
'</span>\n  <span class="value">' +
((__t = ( self.format(x ? m.valueAt(x) : m.lastValue()) )) == null ? '' : __t) +
'</span>\n</li>\n';
 }); ;
__p += '\n';

}
return __p
};