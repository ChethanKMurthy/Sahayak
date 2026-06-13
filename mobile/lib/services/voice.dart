import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_to_text.dart';
import '../i18n.dart';

/// On-device voice: ASR (speech_to_text) + TTS (flutter_tts) in the user's
/// language. When the backend has Bhashini/AWS keys, audio can be routed there
/// instead; on-device is the default privacy/latency path.
class Voice {
  final _stt = SpeechToText();
  final _tts = FlutterTts();
  bool _sttReady = false;

  Future<bool> init() async {
    _sttReady = await _stt.initialize(onError: (_) {}, onStatus: (_) {});
    await _tts.awaitSpeakCompletion(true);
    return _sttReady;
  }

  bool get available => _sttReady;
  bool get listening => _stt.isListening;

  Future<String> listen(String lang, {Duration timeout = const Duration(seconds: 8)}) async {
    if (!_sttReady) return '';
    final completer = <String>[];
    await _stt.listen(
      localeId: I18n.bcp47(lang),
      listenFor: timeout,
      onResult: (r) {
        if (r.finalResult) completer.add(r.recognizedWords);
      },
    );
    // Poll until a final result or timeout.
    final start = DateTime.now();
    while (completer.isEmpty && DateTime.now().difference(start) < timeout) {
      await Future.delayed(const Duration(milliseconds: 150));
      if (!_stt.isListening && completer.isEmpty) break;
    }
    await _stt.stop();
    return completer.isNotEmpty ? completer.first : '';
  }

  Future<void> speak(String text, String lang) async {
    await _tts.setLanguage(I18n.bcp47(lang));
    await _tts.setSpeechRate(0.46);
    await _tts.speak(text);
  }

  Future<void> stop() async {
    await _tts.stop();
    await _stt.stop();
  }
}

/// App-wide singleton so any screen can speak/listen without re-initialising.
class VoiceSingleton {
  static final Voice instance = Voice();
}
