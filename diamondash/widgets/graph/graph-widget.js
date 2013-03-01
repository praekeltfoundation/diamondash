var widgets = diamondash.widgets;

widgets.GraphWidgetModel = widgets.WidgetModel.extend({
  isStatic: false,

  initialize: function(options) {
    options = options || {};

    var self = this,
        metrics = new widgets.GraphWidgetMetricCollection(
          options.metrics || []);

    metrics
      .on('all', function(eventName) { self.trigger(eventName + ':metrics'); })
      .on('change', function() { self.trigger('change'); });

    this.set({
      metrics: metrics,
      domain: 0,
      range: 0
    });
  },

  getMetricModels: function() { return this.get('metrics').models; },

  parse: function(data) {
    this.set({
      domain: data.domain,
      range: data.range
    }, {silent: true});

    var metrics = this.get('metrics');
    
    data.metrics.forEach(function(d) {
      var m = metrics.get(d.name);
      if (typeof m !== 'undefined') {
        m.set('datapoints', d.datapoints, {silent: true});
      }
    });

    this.trigger('change');
  }
});


var maxColors = 10,
    color = d3.scale.category10().domain(d3.range(maxColors)),
    colorCount = 0,
    nextColor = function() { return color(colorCount++ % maxColors); };

widgets.GraphWidgetMetricModel = Backbone.Model.extend({
  idAttribute: 'name',

  initialize: function(options) {
    if (!this.has('datapoints')) {
      this.set('datapoints', []);
    }

    if (!this.has('color')) {
      this.set('color', nextColor());
    }
  },

  bisect: d3.bisector(function(d) { return d.x; }).left,

  getLValue: function(x) {
    var datapoints = this.get('datapoints'),
        v = (datapoints[datapoints.length - 1] || {}).y;

    return typeof v !== "undefined"
      ? v
      : null;
  },

  getValueAt: function(x) {
    var datapoints = this.get('datapoints'),
        i = this.bisect(datapoints, x),
        d = datapoints[i] || {};

    return x === d.x
      ? d.y
      : null;
  }
});

widgets.GraphWidgetMetricCollection = Backbone.Collection.extend({
  model: widgets.GraphWidgetMetricModel
});

var _formatTime = d3.time.format("%d-%m %H:%M"),
    _formatValue = d3.format(".3s");

widgets.GraphWidgetView = widgets.WidgetView.extend({
  svgHeight: 214,
  axisHeight: 24,
  axisMarkerWidth: 128,
  markerCollisionDistance: 60,
  hoverDotSize: 4,
  dottedHoverDotSize: 5,
  dotSize: 3,
  margin: {top: 4, right: 4, bottom: 0, left: 4},

  formatTime: function(t) { return _formatTime(new Date(t)); },
  formatValue: function(v) { return v !== null ? _formatValue(v) : ''; },

  initialize: function(options) {
    var self = this,
        metrics = this.model.getMetricModels(),
        d3el = d3.select(this.el);

    // Parse Config
    // ------------
    if (options.config) {
      var config = options.config;
      this.dotted = config.dotted || false;
    }

    // Dimensions Setup
    // -------------
    var margin = this.margin;
    this.width = this.$el.width();
    this.chartWidth = this.width - margin.left - margin.right;
    this.chartHeight = this.svgHeight
          - this.axisHeight - margin.top - margin.bottom;
    this.axisVPosition = this.svgHeight - this.axisHeight;

    // Chart Setup
    // -----------
    var svg = this.svg = d3el.append('svg')
        .attr('class', 'svg')
        .attr('width', this.width)
        .attr('height', this.svgHeight)
      .append('g')
        .attr('transform', "translate("+margin.left+","+margin.top+")");

    var fx, fy;
    this.fx = fx = d3.time.scale().range([0, this.chartWidth]);
    this.fy = fy = d3.scale.linear().range([this.chartHeight, 0]);

    this.maxTicks = Math.floor(this.chartWidth / this.axisMarkerWidth);
    this.axis = d3.svg.axis()
      .scale(fx)
      .orient('bottom')
      .tickFormat(this.formatTime)
      .ticks(this.maxTicks);

    this.line = d3.svg.line()
      .interpolate('monotone')
      .x(function(d) { return fx(d.x); })
      .y(function(d) { return fy(d.y); });

    var chart = this.chart = svg.append('g')
      .attr('class', 'chart')
      .attr('height', this.chartHeight);

    this.axisLine = svg.append("g")
      .attr('class', 'axis')
      .attr('transform', "translate(0,"+this.axisVPosition+")")
      .call(this.axis);

    // Legend Setup
    // -----------
    var legend = d3el.append('ul')
      .attr('class', 'legend');

    var legendItem = this.legendItem = legend.selectAll('.legend-item')
      .data(metrics, function(d) { return d.get('name'); })
      .enter()
      .append('li')
        .attr('class', 'legend-item');

    this.legendItemSwatch = legendItem.append('span')
      .attr('class', 'legend-item-swatch')
      .style('background-color', function(d) { return d.get('color'); });

    this.legendItemTitles = legendItem.append('span')
      .attr('class', 'legend-item-title-label')
      .text(function(d) { return d.get('title'); });

    this.legendItemValues = legendItem.append('text')
      .attr('class', 'legend-item-value');

    // Hover Setup
    // -----------
    
    // create an overlay to catch events
    this.svg.append('rect')
      .attr('class', 'event-overlay')
      .attr('fill-opacity', 0)
      .attr('width', this.width)
      .attr('height', this.svgHeight)
      .on('mousemove',
          function() { self.focus.call(self, d3.mouse(this)[0]); })
      .on('mouseout',
          function() { self.unfocus.call(self); });

    // Model-View Bindings Setup
    // -------------------------
    this.model.on('change', this.render, this);
  },

  snapX: function(x) {
    var start = this.model.get('domain')[0] || 0,
        step = this.model.get('step'),
        i = Math.round((x - start) / step);

    return start + (step * i);
  },

  buildHoverMarker: function(g) {
    // Replicates the way d3 generates axis time markers.
    // (cloning of one of one of the axis time markers could be done instead,
    // but that is not d3-like).

    g.attr('class', 'hover-marker');

    g.append('line')
      .attr('class', 'tick')
      .attr('y2', 6)
      .attr('x2', 0);

    g.append('text')
      .attr('text-anchor', "middle")
      .attr('dy', ".71em")
      .attr('y', 9)
      .attr('x', 0)
      .attr('fill-opacity', 0);

    return g;
  },

  focus: function(svgX) {
    var fx = this.fx,
        fy = this.fy;
  
    // convert the svg x value to the corresponding time x value, then snap it
    // to the closest timestep
    var x = this.snapX(fx.invert(svgX));
    svgX = fx(x);

    var metrics = this.model.get('metrics');
    var metricValues = metrics.invoke('getValueAt', x);

    // draw hover marker
    var hoverMarker = this.axisLine.selectAll('.hover-marker').data([null]);
    hoverMarker.enter().append('g')
      .call(this.buildHoverMarker)
      .transition().select('text').attr('fill-opacity', 1);
    hoverMarker
      .attr('transform', "translate(" + svgX + ", 0)")
      .select('text').text(this.formatTime(x));

    // hide axis markers colliding with hover marker
    var markerCollisionDistance = this.markerCollisionDistance;
    this.axisLine.selectAll('g')
      .style('fill-opacity', function(d) {
        return Math.abs(fx(d) - svgX) < markerCollisionDistance ? 0 : 1;
      });

    // change legend values
    this.legendItemValues
      .data(metricValues)
      .attr('class', 'hover-legend-item-value')
      .text(this.formatValue);

    // draw dots
    var dots = this.svg.selectAll('.hover-dot')
      .data(_.reject(metricValues, function(d) { return d === null; }));

    dots.enter().append('circle')
      .attr('class', 'hover-dot')
      .style('stroke', function(d, i) { return metrics.at(i).get('color'); })
      .transition()
        .attr('r', this.dotted ? this.dottedHoverDotSize : this.hoverDotSize);

    dots.attr('cx', svgX)
        .attr('cy', fy);
  },

  unfocus: function() {
    this.svg.selectAll('.hover-dot, .hover-marker').remove();
    this.axisLine.selectAll('g').style('fill-opacity', 1);
    this.renderLValues();
    this.legendItemValues.attr('class', 'legend-item-value');
  }, 

  genTickValues: function(start, end, step) {
    var n = (end - start) / step,
        m = this.maxTicks,
        i = 1;

    while (Math.floor(n / i) > m) i++;
    return d3.range(start, end, step * i);
  },

  renderLValues: function() {
    this.legendItemValues
      .data(this.model.get('metrics').invoke('getLValue'))
      .text(this.formatValue);
  },

  render: function() {
    var model = this.model,
        line = this.line,
        metrics = model.getMetricModels(),
        domain = model.get('domain'),
        range = model.get('range'),
        step = model.get('step'),
        fx = this.fx,
        fy = this.fy;

    fx.domain(domain);
    fy.domain(range);

    this.axis.tickValues(this.genTickValues.apply(this, domain.concat([step])));
    this.axisLine.call(this.axis);

    var lines = this.chart.selectAll('.line').data(metrics);
    lines.enter().append('path')
      .attr('class', 'line')
      .style('stroke', function(d) { return d.get('color'); });
    lines.attr('d', function(d) { return line(d.get('datapoints')); });

    if (this.dotted) {
      var dotGroups = this.chart.selectAll('.dot-group').data(metrics);
      dotGroups.enter().append('g')
        .attr('class', 'dot-group')
        .style('fill', function(d) { return d.get('color'); });

      var dots = dotGroups.selectAll('.dot')
        .data(function(d) { return d.get('datapoints'); });
      dots.enter().append('circle')
        .attr('class', 'dot')
        .attr('r', this.dotSize);
      dots
        .attr('cx', function(d) { return fx(d.x); })
        .attr('cy', function(d) { return fy(d.y); });

      //dots.attr('cx', function(d) { return );
      //    .attr('cy', this.fy);
    }

    this.legendItemTitles.text(function(d) { return d.get('title') + ": "; });
    this.renderLValues();
  }
});
