import 'package:flutter/material.dart';
import '../services/storage_service.dart';
import '../services/api_service.dart';
import '../data/bist_stocks.dart';
import 'detail_screen.dart';

class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _searchController = TextEditingController();
  TextEditingController? _activeSearchController;
  List<String> _watchlist = [];
  Map<String, Map<String, dynamic>> _quotes = {};
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _initApp();
  }

  Future<void> _initApp() async {
    await _loadWatchlist();
  }

  Future<void> _loadWatchlist() async {
    if (_watchlist.isEmpty) {
      setState(() => _isLoading = true);
    }
    final list = await StorageService.getWatchlist();
    if (mounted) {
      setState(() {
        _watchlist = list;
      });
    }

    if (list.isEmpty) {
      if (mounted) setState(() => _isLoading = false);
      return;
    }

    // Try batch loading first (fast single request)
    final batchQuotes = await ApiService.getBatchQuotes(list);
    if (batchQuotes != null && batchQuotes.isNotEmpty) {
      if (mounted) {
        setState(() {
          _quotes.addAll(batchQuotes);
          _isLoading = false;
        });
      }
      return;
    }

    // Fallback: fetch concurrently
    final futures = list.map((s) => ApiService.getQuote(s)).toList();
    final results = await Future.wait(futures);
    if (mounted) {
      setState(() {
        for (int i = 0; i < list.length; i++) {
          if (results[i] != null) {
            _quotes[list[i]] = results[i]!;
          }
        }
        _isLoading = false;
      });
    }
  }

  Future<void> _addSymbol(String symbol, {TextEditingController? controller}) async {
    final upperSymbol = symbol.toUpperCase().trim();
    if (upperSymbol.isEmpty) return;

    final targetController = controller ?? _activeSearchController ?? _searchController;

    if (_watchlist.contains(upperSymbol)) {
      targetController.clear();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('$upperSymbol zaten listenizde ekli.'),
            duration: const Duration(seconds: 2),
          ),
        );
      }
      return;
    }

    await StorageService.addSymbol(upperSymbol);

    if (mounted) {
      setState(() {
        if (!_watchlist.contains(upperSymbol)) {
          _watchlist.add(upperSymbol);
        }
      });
      targetController.clear();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('$upperSymbol listenize eklendi.'),
          backgroundColor: Colors.blueAccent,
          duration: const Duration(seconds: 2),
        ),
      );
    }

    final quote = await ApiService.getQuote(upperSymbol);
    if (quote != null && mounted) {
      setState(() {
        _quotes[upperSymbol] = quote;
      });
    }
  }

  Future<void> _removeSymbol(String symbol) async {
    await StorageService.removeSymbol(symbol);
    if (mounted) {
      setState(() {
        _watchlist.remove(symbol);
        _quotes.remove(symbol);
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('$symbol listeden çıkarıldı.'),
          duration: const Duration(seconds: 2),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0C),
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.trending_up, color: Colors.blueAccent, size: 26),
            SizedBox(width: 8),
            Text('BIST Dashboard', style: TextStyle(fontWeight: FontWeight.bold)),
          ],
        ),
        backgroundColor: const Color(0xFF151518),
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined, color: Colors.white70),
            tooltip: 'Ayarlar',
            onPressed: () => _showSettingsBottomSheet(context),
          ),
        ],
      ),
      body: Column(
        children: [
          _buildSearchBar(),
          Expanded(
            child: _isLoading && _watchlist.isEmpty
                ? const Center(child: CircularProgressIndicator(color: Colors.blueAccent))
                : _watchlist.isEmpty
                    ? const Center(child: Text('Listeniz boş, hisse ekleyin.', style: TextStyle(color: Colors.grey)))
                    : _buildWatchlist(),
          ),
        ],
      ),
    );
  }

  Widget _buildSearchBar() {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Container(
        decoration: BoxDecoration(
          color: const Color(0xFF1E1E24),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.white10),
        ),
        child: Autocomplete<String>(
          optionsBuilder: (TextEditingValue textEditingValue) {
            if (textEditingValue.text == '') {
              return const Iterable<String>.empty();
            }
            return BistStocks.symbols.where((String option) {
              return option.contains(textEditingValue.text.toUpperCase());
            });
          },
          onSelected: (String selection) {
            _addSymbol(selection, controller: _activeSearchController);
          },
          fieldViewBuilder: (BuildContext context, TextEditingController textEditingController, FocusNode focusNode, VoidCallback onFieldSubmitted) {
            _activeSearchController = textEditingController;
            return TextField(
              controller: textEditingController,
              focusNode: focusNode,
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                hintText: 'Hisse Ara (örn. THYAO)...',
                hintStyle: const TextStyle(color: Colors.white54),
                border: InputBorder.none,
                prefixIcon: const Icon(Icons.search, color: Colors.white54),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.add, color: Colors.blueAccent),
                  onPressed: () => _addSymbol(textEditingController.text, controller: textEditingController),
                ),
                contentPadding: const EdgeInsets.symmetric(vertical: 14),
              ),
              onSubmitted: (String value) {
                onFieldSubmitted();
                _addSymbol(value, controller: textEditingController);
              },
            );
          },
          optionsViewBuilder: (BuildContext context, AutocompleteOnSelected<String> onSelected, Iterable<String> options) {
            return Align(
              alignment: Alignment.topLeft,
              child: Material(
                color: Colors.transparent,
                child: Container(
                  width: MediaQuery.of(context).size.width - 32,
                  margin: const EdgeInsets.only(top: 8),
                  constraints: const BoxConstraints(maxHeight: 250),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1E1E24),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.white10),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.5),
                        blurRadius: 10,
                        offset: const Offset(0, 5),
                      )
                    ]
                  ),
                  child: ListView.builder(
                    padding: EdgeInsets.zero,
                    shrinkWrap: true,
                    itemCount: options.length,
                    itemBuilder: (BuildContext context, int index) {
                      final String option = options.elementAt(index);
                      return InkWell(
                        onTap: () {
                          onSelected(option);
                        },
                        child: Container(
                          padding: const EdgeInsets.all(16.0),
                          decoration: const BoxDecoration(
                            border: Border(bottom: BorderSide(color: Colors.white10))
                          ),
                          child: Text(
                            option,
                            style: const TextStyle(color: Colors.white, fontSize: 16),
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildWatchlist() {
    return RefreshIndicator(
      onRefresh: _loadWatchlist,
      color: Colors.blueAccent,
      backgroundColor: const Color(0xFF1E1E24),
      child: ListView.builder(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.symmetric(horizontal: 16),
      itemCount: _watchlist.length,
      itemBuilder: (context, index) {
        final symbol = _watchlist[index];
        final quote = _quotes[symbol];

        return Card(
          color: const Color(0xFF151518),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: const BorderSide(color: Colors.white10),
          ),
          margin: const EdgeInsets.only(bottom: 12),
          child: ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            title: Text(
              symbol,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.white),
            ),
            subtitle: quote == null
                ? const Text('Yükleniyor...', style: TextStyle(color: Colors.grey))
                : Text(
                    '₺${quote['price']}',
                    style: const TextStyle(fontSize: 16, color: Colors.white70),
                  ),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (quote != null)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: quote['change_percent'] >= 0 ? Colors.green.withOpacity(0.2) : Colors.red.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      '${quote['change_percent'] >= 0 ? '+' : ''}${quote['change_percent']}%',
                      style: TextStyle(
                        color: quote['change_percent'] >= 0 ? Colors.greenAccent : Colors.redAccent,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                const SizedBox(width: 8),
                IconButton(
                  icon: const Icon(Icons.delete_outline, color: Colors.redAccent),
                  onPressed: () => _removeSymbol(symbol),
                ),
              ],
            ),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => DetailScreen(symbol: symbol, initialQuote: quote),
                ),
              );
            },
          ),
        );
      },
    ),
    );
  }

  void _showSettingsBottomSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF151518),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (bottomSheetContext) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.settings, color: Colors.blueAccent),
                        SizedBox(width: 10),
                        Text(
                          'Ayarlar',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                    IconButton(
                      icon: const Icon(Icons.close, color: Colors.white54),
                      onPressed: () => Navigator.pop(bottomSheetContext),
                    ),
                  ],
                ),
                const Divider(color: Colors.white10, height: 24),
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 4, vertical: 8),
                  child: Text(
                    'VERİ VE DÜZEN',
                    style: TextStyle(
                      color: Colors.white38,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.1,
                    ),
                  ),
                ),
                Card(
                  color: const Color(0xFF1E1E24),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                    side: const BorderSide(color: Colors.white10),
                  ),
                  child: ListTile(
                    leading: Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.redAccent.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Icon(Icons.delete_forever_outlined, color: Colors.redAccent),
                    ),
                    title: const Text(
                      'Verileri Sil',
                      style: TextStyle(
                        color: Colors.redAccent,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    subtitle: const Text(
                      'Seçili hisseler, çerezler ve önbellekteki tüm verileri sıfırlar.',
                      style: TextStyle(color: Colors.white54, fontSize: 12),
                    ),
                    trailing: const Icon(Icons.chevron_right, color: Colors.redAccent),
                    onTap: () {
                      Navigator.pop(bottomSheetContext);
                      _confirmClearData(context);
                    },
                  ),
                ),
                const SizedBox(height: 16),
                const Center(
                  child: Text(
                    'Versiyon (12.08.2026-18.20)',
                    style: TextStyle(color: Colors.white38, fontSize: 12),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Future<void> _confirmClearData(BuildContext context) async {
    final messenger = ScaffoldMessenger.of(context);
    final bool? confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          backgroundColor: const Color(0xFF1E1E24),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: const BorderSide(color: Colors.white10),
          ),
          title: const Row(
            children: [
              Icon(Icons.warning_amber_rounded, color: Colors.redAccent, size: 28),
              SizedBox(width: 10),
              Text(
                'Verileri Sil',
                style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          content: const Text(
            'Seçili tüm hisseleriniz, önbellek ve çerez verileri kalıcı olarak sıfırlanacaktır.\n\nBu işlemi onaylıyor musunuz?',
            style: TextStyle(color: Colors.white70, fontSize: 14),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('İptal', style: TextStyle(color: Colors.white54)),
            ),
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.redAccent,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              onPressed: () => Navigator.pop(dialogContext, true),
              icon: const Icon(Icons.delete_forever, size: 18),
              label: const Text('Evet, Sil'),
            ),
          ],
        );
      },
    );

    if (confirmed == true) {
      await StorageService.clearAllData();
      if (!mounted) return;
      setState(() {
        _watchlist.clear();
        _quotes.clear();
      });
      await _loadWatchlist();
      messenger.showSnackBar(
        const SnackBar(
          content: Row(
            children: [
              Icon(Icons.check_circle_outline, color: Colors.white),
              SizedBox(width: 8),
              Text('Tüm önbellek ve veriler sıfırlandı, varsayılan BİST 30 yüklendi.'),
            ],
          ),
          backgroundColor: Colors.blueAccent,
          duration: Duration(seconds: 3),
        ),
      );
    }
  }
}
