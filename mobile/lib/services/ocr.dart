import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'pii.dart';

/// On-device OCR + lightweight document classification + field extraction.
/// Everything here runs on the phone (ML Kit); only masked fields are sent up.
class OnDeviceOcr {
  final _recognizer = TextRecognizer(script: TextRecognitionScript.devanagiri);

  Future<OcrResult> readImage(String imagePath) async {
    final input = InputImage.fromFilePath(imagePath);
    final recognized = await _recognizer.processImage(input);
    final raw = recognized.text;

    // Average ML Kit element confidence as a quality proxy.
    final confs = <double>[];
    for (final b in recognized.blocks) {
      for (final l in b.lines) {
        for (final e in l.elements) {
          if (e.confidence != null) confs.add(e.confidence!);
        }
      }
    }
    final quality = confs.isEmpty ? 0.6 : confs.reduce((a, b) => a + b) / confs.length;

    final type = _classify(raw);
    final fields = Pii.scrub(_extract(raw, type));
    final last4 = Pii.aadhaarLast4(raw);
    if (last4 != null) fields['aadhaar_last4'] = last4;

    return OcrResult(
      type: type,
      ocrQuality: quality,
      fields: fields,
      recaptureHint: quality < 0.6
          ? 'The text is hard to read — move the document into the frame and avoid glare.'
          : null,
    );
  }

  String _classify(String text) {
    final t = text.toLowerCase();
    if (t.contains('aadhaar') || t.contains('आधार') || t.contains('uidai')) return 'aadhaar';
    if (t.contains('ration') || t.contains('राशन')) return 'ration_card';
    if (t.contains('marks') || t.contains('marksheet') || t.contains('अंक')) return 'marksheet';
    if (t.contains('income') || t.contains('आय')) return 'income_cert';
    if (t.contains('caste') || t.contains('जाति')) return 'caste_cert';
    if (t.contains('ifsc') || t.contains('account')) return 'bank_passbook';
    if (t.contains('khasra') || t.contains('khatauni') || t.contains('7/12')) return 'land_record';
    return 'unknown';
  }

  /// Best-effort label:value extraction. The cloud LLM (Grok) refines this;
  /// on-device we grab the obvious fields so the privacy path still works offline.
  Map<String, dynamic> _extract(String text, String type) {
    final fields = <String, dynamic>{};
    final dob = RegExp(r'(\d{2}[/-]\d{2}[/-]\d{4})').firstMatch(text);
    if (dob != null) fields['dob'] = dob.group(1);
    final gender = RegExp(r'\b(male|female|पुरुष|महिला)\b', caseSensitive: false).firstMatch(text);
    if (gender != null) {
      final g = gender.group(1)!.toLowerCase();
      fields['gender'] = (g == 'पुरुष' || g == 'male') ? 'male' : 'female';
    }
    final ifsc = RegExp(r'\b([A-Z]{4}0[A-Z0-9]{6})\b').firstMatch(text);
    if (ifsc != null) fields['ifsc'] = ifsc.group(1);
    return fields;
  }

  void dispose() => _recognizer.close();
}

class OcrResult {
  final String type;
  final double ocrQuality;
  final Map<String, dynamic> fields;
  final String? recaptureHint;
  OcrResult({required this.type, required this.ocrQuality, required this.fields, this.recaptureHint});

  Map<String, dynamic> toCaptureDoc(String id) => {
        'id': id,
        'type': type,
        'ocr_quality': ocrQuality,
        'fields': fields.entries
            .map((e) => {'key': e.key, 'value': e.value, 'ocr_confidence': ocrQuality})
            .toList(),
      };
}
