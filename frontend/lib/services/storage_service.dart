import 'package:shared_preferences/shared_preferences.dart';
import '../data/bist_stocks.dart';

class StorageService {
  static const String _watchlistKey = 'watchlist_symbols';

  static Future<void> clearCacheExceptWatchlist() async {
    final prefs = await SharedPreferences.getInstance();
    final keys = prefs.getKeys();
    for (String key in keys) {
      if (key != _watchlistKey) {
        await prefs.remove(key);
      }
    }
  }

  static Future<void> clearAllData() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
  }

  static Future<List<String>> getWatchlist() async {
    final prefs = await SharedPreferences.getInstance();
    final list = prefs.getStringList(_watchlistKey);
    
    if (list == null) {
      // Return BIST 30 for the first time launch
      await prefs.setStringList(_watchlistKey, BistStocks.bist30);
      return BistStocks.bist30;
    }
    
    return list;
  }

  static Future<void> addSymbol(String symbol) async {
    final prefs = await SharedPreferences.getInstance();
    final list = prefs.getStringList(_watchlistKey) ?? [];
    if (!list.contains(symbol)) {
      list.add(symbol);
      await prefs.setStringList(_watchlistKey, list);
    }
  }

  static Future<void> removeSymbol(String symbol) async {
    final prefs = await SharedPreferences.getInstance();
    final list = prefs.getStringList(_watchlistKey) ?? [];
    list.remove(symbol);
    await prefs.setStringList(_watchlistKey, list);
  }
}
