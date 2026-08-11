import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/api_service.dart';
import '../widgets/native_chart_widget.dart';

class DetailScreen extends StatefulWidget {
  final String symbol;
  final Map<String, dynamic>? initialQuote;
  
  const DetailScreen({Key? key, required this.symbol, this.initialQuote}) : super(key: key);

  @override
  _DetailScreenState createState() => _DetailScreenState();
}

class _DetailScreenState extends State<DetailScreen> {
  bool _isLoading = true;
  Map<String, dynamic>? _quote;
  Map<String, dynamic>? _signals;
  Map<String, dynamic>? _news;
  Map<String, dynamic>? _kapReports;
  Map<String, dynamic>? _brokerTargets;
  
  List<ChartData>? _chartData;
  String _selectedInterval = '1d';
  bool _isChartLoading = false;

  @override
  void initState() {
    super.initState();
    _quote = widget.initialQuote;
    _fetchData();
  }

  List<ChartData> _parseChartData(Map<String, dynamic>? res) {
    if (res != null && res['data'] != null) {
      final List<dynamic> rawData = res['data'];
      return rawData.map((e) => ChartData(
        time: DateTime.fromMillisecondsSinceEpoch((e['time'] as num).toInt()),
        open: (e['open'] as num).toDouble(),
        high: (e['high'] as num).toDouble(),
        low: (e['low'] as num).toDouble(),
        close: (e['close'] as num).toDouble(),
        volume: (e['volume'] as num).toDouble(),
        ema: e['ema'] != null ? (e['ema'] as num).toDouble() : null,
        sma50: e['sma_50'] != null ? (e['sma_50'] as num).toDouble() : null,
        volumeMa: e['volume_ma'] != null ? (e['volume_ma'] as num).toDouble() : null,
        bollingerUpper: e['bollinger_upper'] != null ? (e['bollinger_upper'] as num).toDouble() : null,
        bollingerMiddle: e['bollinger_middle'] != null ? (e['bollinger_middle'] as num).toDouble() : null,
        bollingerLower: e['bollinger_lower'] != null ? (e['bollinger_lower'] as num).toDouble() : null,
        rsi: e['rsi'] != null ? (e['rsi'] as num).toDouble() : null,
        macd: e['macd'] != null ? (e['macd'] as num).toDouble() : null,
        macdSignal: e['macd_signal'] != null ? (e['macd_signal'] as num).toDouble() : null,
        macdHist: e['macd_hist'] != null ? (e['macd_hist'] as num).toDouble() : null,
      )).toList();
    }
    return [];
  }

  Future<void> _fetchData() async {
    setState(() => _isLoading = true);
    final results = await Future.wait([
      ApiService.getSignals(widget.symbol),
      ApiService.getNews(widget.symbol),
      ApiService.getKapReports(widget.symbol),
      ApiService.getBrokerTargets(widget.symbol),
      ApiService.getChartData(widget.symbol, interval: _selectedInterval),
      ApiService.getQuote(widget.symbol),
    ]);

    if (mounted) {
      setState(() {
        _signals = results[0];
        _news = results[1];
        _kapReports = results[2];
        _brokerTargets = results[3];
        if (results[5] != null) {
          _quote = results[5];
        }
        _chartData = _parseChartData(results[4]);
        _isLoading = false;
      });
    }
  }

  Future<void> _onIntervalChanged(String newInterval) async {
    if (_selectedInterval != newInterval) {
      setState(() {
        _selectedInterval = newInterval;
        _isChartLoading = true;
      });

      final result = await ApiService.getChartData(widget.symbol, interval: newInterval);

      if (mounted) {
        setState(() {
          _chartData = _parseChartData(result);
          _isChartLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0C),
      appBar: AppBar(
        titleSpacing: 0,
        backgroundColor: const Color(0xFF151518),
        elevation: 0,
        title: SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                widget.symbol,
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.white),
              ),
              if (_quote != null && _quote!['price'] != null) ...[
                const SizedBox(width: 8),
                Text(
                  '₺${_quote!['price']}',
                  style: const TextStyle(fontSize: 15, color: Colors.white),
                ),
                const SizedBox(width: 6),
                Builder(
                  builder: (context) {
                    final num changePct = _quote!['change_percent'] ?? 0;
                    final bool isPositive = changePct >= 0;
                    final Color color = isPositive ? Colors.greenAccent : Colors.redAccent;
                    final String sign = isPositive ? '+' : '';
                    return Text(
                      '($sign$changePct%)',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                        color: color,
                      ),
                    );
                  },
                ),
              ],
            ],
          ),
        ),
        actions: [
          if (_quote != null && _quote!['name'] != null && (_quote!['name'] as String).isNotEmpty)
            Container(
              alignment: Alignment.centerRight,
              constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.4),
              padding: const EdgeInsets.only(right: 16.0, left: 8.0),
              child: Text(
                _quote!['name'],
                style: const TextStyle(fontSize: 13, color: Colors.white60, fontWeight: FontWeight.w500),
                overflow: TextOverflow.ellipsis,
                maxLines: 1,
              ),
            ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.blueAccent))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Stack(
                    children: [
                      if (_chartData != null && _chartData!.isNotEmpty)
                        NativeChartWidget(
                          symbol: widget.symbol,
                          data: _chartData!,
                          selectedInterval: _selectedInterval,
                          onIntervalChanged: _onIntervalChanged,
                        )
                      else
                        Container(
                          height: 480,
                          decoration: BoxDecoration(
                            color: const Color(0xFF151518),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: Colors.white10),
                          ),
                          child: const Center(child: Text("Grafik verisi bulunamadı", style: TextStyle(color: Colors.white54))),
                        ),
                      if (_isChartLoading)
                        Positioned.fill(
                          child: Container(
                            decoration: BoxDecoration(
                              color: Colors.black45,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Center(
                              child: CircularProgressIndicator(color: Colors.blueAccent),
                            ),
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  _buildSectionTitle('Teknik Analiz (TradingView)'),
                  _buildSignalsSection(),
                  const SizedBox(height: 24),
                  _buildSectionTitle('Banka / Aracı Kurum Hedefleri'),
                  _buildBrokerTargetsSection(),
                  const SizedBox(height: 24),
                  _buildSectionTitle('KAP Raporları'),
                  _buildKapReportsSection(),
                  const SizedBox(height: 24),
                  _buildSectionTitle('Haberler'),
                  _buildNewsSection(),
                ],
              ),
            ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: Text(
        title,
        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.blueAccent),
      ),
    );
  }



  Widget _buildSignalsSection() {
    if (_signals == null || _signals!['timeframes'] == null) {
      return const Text('Sinyal verisi bulunamadı.', style: TextStyle(color: Colors.white54));
    }
    
    final timeframes = _signals!['timeframes'] as Map<String, dynamic>;
    
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: timeframes.entries.map((entry) {
        final label = entry.key;
        final data = entry.value;
        
        if (data['error'] != null) {
          return const SizedBox.shrink(); // Skip errors
        }
        
        final recommendation = data['summary']['RECOMMENDATION'] ?? 'N/A';
        Color recColor = Colors.grey;
        if (recommendation == 'STRONG_BUY' || recommendation == 'BUY') recColor = Colors.greenAccent;
        if (recommendation == 'STRONG_SELL' || recommendation == 'SELL') recColor = Colors.redAccent;
        
        String displayRec = recommendation
            .replaceAll('STRONG_BUY', 'GÜÇLÜ AL')
            .replaceAll('BUY', 'AL')
            .replaceAll('STRONG_SELL', 'GÜÇLÜ SAT')
            .replaceAll('SELL', 'SAT')
            .replaceAll('NEUTRAL', 'NÖTR');
            
        return Container(
          width: (MediaQuery.of(context).size.width - 40) / 2, // 2 columns
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: const Color(0xFF151518),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.white10),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: const TextStyle(color: Colors.white70, fontSize: 14)),
              const SizedBox(height: 4),
              Text(
                displayRec,
                style: TextStyle(color: recColor, fontWeight: FontWeight.bold, fontSize: 15),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  Widget _buildBrokerTargetsSection() {
    if (_brokerTargets == null || _brokerTargets!['targets'] == null) {
      return const Text('Hedef fiyat bulunamadı.', style: TextStyle(color: Colors.white54));
    }
    
    final targets = _brokerTargets!['targets'] as List;
    if (targets.isEmpty) {
      return const Text('Hedef fiyat bulunamadı.', style: TextStyle(color: Colors.white54));
    }

    double total = 0;
    int count = 0;
    for (var t in targets) {
      final price = (t['target_price'] ?? 0).toDouble();
      if (price > 0) {
        total += price;
        count++;
      }
    }
    
    double average = count > 0 ? total / count : 0.0;
    
    List<Widget> children = [];
    if (count > 0) {
      children.add(
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 8.0),
          child: Column(
            children: [
              Text(
                'Ortalama Beklenti: ₺${average.toStringAsFixed(2)}',
                style: const TextStyle(
                  color: Colors.greenAccent,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              const Divider(color: Colors.white24, thickness: 1),
              const SizedBox(height: 8),
            ],
          ),
        ),
      );
    }

    children.addAll(targets.map((t) {
      return Card(
        color: const Color(0xFF151518),
        margin: const EdgeInsets.only(bottom: 8),
        child: ListTile(
          title: Text(t['broker'], style: const TextStyle(color: Colors.white)),
          subtitle: Text(t['date'], style: const TextStyle(color: Colors.white54)),
          trailing: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text('₺${t['target_price']}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
              Text(t['recommendation'], style: const TextStyle(color: Colors.blueAccent)),
            ],
          ),
        ),
      );
    }).toList());

    return Column(
      children: children,
    );
  }

  Widget _buildKapReportsSection() {
    if (_kapReports == null || _kapReports!['reports'] == null) {
      return const Text('KAP verisi bulunamadı.', style: TextStyle(color: Colors.white54));
    }
    
    final reports = _kapReports!['reports'] as List;
    return Column(
      children: reports.map((r) {
        return Card(
          color: const Color(0xFF151518),
          margin: const EdgeInsets.only(bottom: 8),
          child: ListTile(
            title: Text(r['title'], style: const TextStyle(color: Colors.white)),
            subtitle: Text(r['date'], style: const TextStyle(color: Colors.white54)),
            trailing: const Icon(Icons.open_in_new, color: Colors.blueAccent, size: 20),
            onTap: () async {
              final url = Uri.parse(r['link'] ?? r['url'] ?? '');
              if (await canLaunchUrl(url)) {
                await launchUrl(url);
              }
            },
          ),
        );
      }).toList(),
    );
  }
  
  Widget _buildNewsSection() {
    if (_news == null || _news!['news'] == null) {
      return const Text('Haber bulunamadı.', style: TextStyle(color: Colors.white54));
    }
    
    final newsList = _news!['news'] as List;
    return Column(
      children: newsList.map((n) {
        return Card(
          color: const Color(0xFF151518),
          margin: const EdgeInsets.only(bottom: 8),
          child: ListTile(
            title: Text(n['title'], style: const TextStyle(color: Colors.white)),
            subtitle: Text(n['source'], style: const TextStyle(color: Colors.white54)),
            trailing: const Icon(Icons.arrow_forward_ios, color: Colors.white24, size: 16),
            onTap: () async {
              final url = Uri.parse(n['url'] ?? '');
              if (await canLaunchUrl(url)) {
                await launchUrl(url);
              }
            },
          ),
        );
      }).toList(),
    );
  }
}
