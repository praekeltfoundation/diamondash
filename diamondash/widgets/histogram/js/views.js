diamondash.widgets.histogram.views = function() {
  var chart = diamondash.widgets.chart,
      widgets = diamondash.widgets;

  var HistogramView = chart.views.XYChartView.extend({
    height: 278,
    barPadding: 2,
    format: {value: d3.format(".1s")},

    initialize: function() {
      HistogramView.__super__.initialize.call(this);
    },

    render: function() {
      HistogramView.__super__.render.call(this);

      var self = this;
      var metric = this.model.get('metrics').at(0);
      var bucketSize = this.model.get('bucket_size');
      var maxY = this.dims.height() - this.axisHeight;
      var barWidth = this.fx(bucketSize) - this.fx(0) - this.barPadding;

      function data(d) {
        return [d];
      }


      function key(d) {
        return d.x;
      }

      var bar = this.svg.selectAll('.bar')
        .data(metric.get('datapoints'), key);

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
        .style('fill', metric.get('color'))
        .attr('width', barWidth)
        .attr('height', function(d) {
          return maxY - self.fy(d.y);
        });

      var text = bar.selectAll('text').data(data, key);
      text.enter().append('text')
        .attr('class', 'value')
        .attr("text-anchor", "middle")
        .attr("dy", ".75em")
        .attr("y", 6);

      text
          .attr("x", barWidth / 2)
          .text(function(d) {
            return self.format.value(d.y);
          });

      this.$el.append($(this.svg.node()));
      return this;
    }
  });

  widgets.registry.views.add('histogram', HistogramView);

  return {
    HistogramView: HistogramView
  };
}.call(this);
