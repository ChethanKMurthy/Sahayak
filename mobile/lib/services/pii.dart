/// On-device PII safety. Runs BEFORE anything leaves the phone — the full
/// 12-digit Aadhaar number is masked to last-4 and never transmitted.
class Pii {
  static final _aadhaar = RegExp(r'\b(\d{4})\s?-?(\d{4})\s?-?(\d{4})\b');

  static String maskText(String text) =>
      text.replaceAllMapped(_aadhaar, (m) => 'XXXX-XXXX-${m.group(3)}');

  static String? aadhaarLast4(String text) {
    final m = _aadhaar.firstMatch(text);
    return m?.group(3);
  }

  /// Scrub a field map before egress: convert any full Aadhaar to last-4 only.
  static Map<String, dynamic> scrub(Map<String, dynamic> fields) {
    final out = <String, dynamic>{};
    fields.forEach((k, v) {
      final key = k.toLowerCase();
      if ((key == 'aadhaar' || key == 'aadhaar_number' || key == 'uid') && v is String) {
        out['aadhaar_last4'] = aadhaarLast4(v) ?? (v.length >= 4 ? v.substring(v.length - 4) : v);
      } else if (v is String) {
        out[k] = maskText(v);
      } else {
        out[k] = v;
      }
    });
    return out;
  }
}
