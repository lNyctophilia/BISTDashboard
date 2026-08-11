// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'package:flutter/material.dart';
import 'dart:ui_web' as ui_web;

class TVChartWidget extends StatefulWidget {
  final String symbol;

  const TVChartWidget({Key? key, required this.symbol}) : super(key: key);

  @override
  _TVChartWidgetState createState() => _TVChartWidgetState();
}

class _TVChartWidgetState extends State<TVChartWidget> {
  late String viewType;

  @override
  void initState() {
    super.initState();
    viewType = 'tv-chart-${widget.symbol}-${DateTime.now().millisecondsSinceEpoch}';
    
    // TradingView Advanced Chart Widget HTML
    final tvHtml = '''
    <!DOCTYPE html>
    <html>
    <head>
      <meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,minimum-scale=1.0">
      <style>body {margin: 0; padding: 0; background-color: #0A0A0C; overflow: hidden;}</style>
    </head>
    <body>
      <div class="tradingview-widget-container" style="height:100vh;width:100vw">
        <div id="tradingview_chart" style="height:100%;width:100%"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.widget(
        {
          "autosize": true,
          "symbol": "BIST:${widget.symbol.replaceAll('.IS', '').trim().toUpperCase()}",
          "interval": "W",
          "timezone": "Europe/Istanbul",
          "theme": "dark",
          "style": "1",
          "locale": "tr",
          "enable_publishing": false,
          "backgroundColor": "#151518",
          "hide_top_toolbar": false,
          "hide_legend": false,
          "save_image": false,
          "container_id": "tradingview_chart",
          "studies": [
            "Volume@tv-basicstudies",
            "MAExp@tv-basicstudies"
          ],
          "studies_overrides": {
            "volume.show ma": true,
            "volume.volume ma.color": "#FF0000"
          }
        }
        );
        </script>
      </div>
    </body>
    </html>
    ''';

    final iframe = html.IFrameElement()
      ..width = '100%'
      ..height = '100%'
      ..src = 'data:text/html;charset=utf-8,' + Uri.encodeComponent(tvHtml)
      ..style.border = 'none';

    ui_web.platformViewRegistry.registerViewFactory(
      viewType,
      (int viewId) => iframe,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 400,
      decoration: BoxDecoration(
        color: const Color(0xFF151518),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white10),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: HtmlElementView(viewType: viewType),
      ),
    );
  }
}

