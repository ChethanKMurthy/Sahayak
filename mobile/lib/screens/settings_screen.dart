import 'package:flutter/material.dart';

/// App settings — language selection across the 7 supported languages.
class SettingsScreen extends StatefulWidget {
  final String currentLang;
  final ValueChanged<String>? onLangChanged;

  const SettingsScreen({super.key, this.currentLang = 'hi', this.onLangChanged});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  static const Map<String, String> _langs = {
    'hi': 'हिन्दी',
    'en': 'English',
    'kn': 'ಕನ್ನಡ',
    'ta': 'தமிழ்',
    'te': 'తెలుగు',
    'mr': 'मराठी',
    'bn': 'বাংলা',
  };

  late String _lang = widget.currentLang;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        children: [
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: Text('Language', style: TextStyle(fontWeight: FontWeight.w600)),
          ),
          for (final e in _langs.entries)
            RadioListTile<String>(
              value: e.key,
              groupValue: _lang,
              title: Text(e.value),
              subtitle: Text(e.key.toUpperCase()),
              onChanged: (v) {
                if (v == null) return;
                setState(() => _lang = v);
                widget.onLangChanged?.call(v);
              },
            ),
        ],
      ),
    );
  }
}
