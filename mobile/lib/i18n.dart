import 'dart:convert';
import 'package:flutter/services.dart';

/// Loads the shared 7-language UI strings (synced from /shared via scripts/sync-shared.sh).
class I18n {
  static Map<String, dynamic> _bundle = {};

  static const languages = [
    ("hi", "हिन्दी"), ("en", "English"), ("kn", "ಕನ್ನಡ"),
    ("ta", "தமிழ்"), ("te", "తెలుగు"), ("mr", "मराठी"), ("bn", "বাংলা"),
  ];

  static Future<void> load() async {
    final raw = await rootBundle.loadString('assets/i18n/strings.json');
    _bundle = json.decode(raw) as Map<String, dynamic>;
  }

  static String t(String key, String lang) {
    final entry = _bundle[key] as Map<String, dynamic>?;
    if (entry == null) return key;
    return (entry[lang] ?? entry['en'] ?? key).toString();
  }

  static String loc(Map<String, dynamic>? map, String lang) {
    if (map == null) return "";
    return (map[lang] ?? map['en'] ?? (map.values.isNotEmpty ? map.values.first : "")).toString();
  }

  static String bcp47(String lang) => switch (lang) {
        "hi" => "hi-IN", "en" => "en-IN", "kn" => "kn-IN", "ta" => "ta-IN",
        "te" => "te-IN", "mr" => "mr-IN", "bn" => "bn-IN", _ => "en-IN",
      };
}
