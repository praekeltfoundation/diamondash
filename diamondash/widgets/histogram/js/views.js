diamondash.widgets.histogram.views = function() {
  var utils = diamondash.utils,
      chart = diamondash.widgets.chart,
      widgets = diamondash.widgets;

  var HistogramView = chart.views.XYChartView.extend({
    height: 278,
    topMargin: 14,
    barPadding: 2,
    format: {
      short: d3.format(".2s"),
      long: d3.format(",f")
    },

    initialize: function() {
      HistogramView.__super__.initialize.call(this);
      this.dims.set('margin', _.extend(this.dims.get('margin'), {
        top: this.topMargin
      }));
      utils.bindEvents(this.bindings, this);
    },

    draw: function() {
      var self = this;
      var metric = this.model.get('metrics').at(0);
      var bucketSize = this.model.get('bucket_size');
      var maxY = this.fy.range()[0];
      var barWidth = this.fx(bucketSize) - this.fx(0) - this.barPadding;

      function data(d) {
        return [d];
      }

      function key(d) {
        return d.x;
      }

      var bar = this.canvas.selectAll('.bar')
        .data(metric.get('datapoints').slice(1), key);

      bar.enter().append('g')
        .attr('class', 'bar');

      bar.exit().remove();

      bar.attr('transform', function(d) {
        var x = self.fx(d.x - bucketSize);
        var y = self.fy(d.y);
        return "translate(" + x + "," + y + ")";
      });

      var rect = bar.selectAll('rect').data(data, key);
      rect.enter().append('rect');

      rect
        .style('fill', this.color(metric))
        .style('pointer-events', 'none')
        .attr('width', barWidth)
        .attr('height', function(d) {
          return maxY - self.fy(d.y);
        });

      var text = bar.selectAll('.value')
        .data(data, key);

      text.enter().append('text')
        .attr('class', 'value')
        .attr("dy", ".75em");

      text
        .attr("x", barWidth / 2)
        .attr("y", 6)
        .text(function(d) {
          return self.format.short(d.y);
        });

      this.svg.selectAll('.hover.bar .value')
        .attr("y", -15)
        .text(function(d) {
          return self.format.long(d.y);
        });
    },

    render: function() {
      HistogramView.__super__.render.call(this);
      this.draw();
      this.$el.append($(this.svg.node()));
      return this;
    },

    bindings: {
      'hover': function(position) {
        var bucketSize = this.model.get('bucket_size');

        function match(d) {
          return d.x === (position.x + bucketSize);
        }

        this.svg.selectAll('.bar')
          .sort(function(d) {
            return match(d)
              ? 1
              : 0;
          })
          .attr('class', function(d) {
            return match(d)
              ? 'hover bar'
              : 'not-hover bar';
          });

        this.draw();
      },

      'unhover': function() {
        this.svg.selectAll('.bar')
          .attr('class', 'bar');

        this.draw();
      }
    }
  });

  widgets.registry.views.add('histogram', HistogramView);

  return {
    HistogramView: HistogramView
  };
}.call(this);
