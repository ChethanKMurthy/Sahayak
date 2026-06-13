import 'dart:convert';
import 'package:http/http.dart' as http;
import 'models.dart';

/// Talks to the FastAPI backend.
/// On the Android emulator, the host machine is reachable at 10.0.2.2.
/// Override with --dart-define=API_BASE=http://<lan-ip>:8000 for a real device.
class Api {
  static const base = String.fromEnvironment('API_BASE', defaultValue: 'http://10.0.2.2:8000');

  Future<Map<String, dynamic>> _get(String path) async {
    final r = await http.get(Uri.parse('$base$path'));
    if (r.statusCode >= 400) throw Exception('${r.statusCode}: ${r.body}');
    return json.decode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> _post(String path, Map<String, dynamic> body) async {
    final r = await http.post(Uri.parse('$base$path'),
        headers: {'Content-Type': 'application/json'}, body: json.encode(body));
    if (r.statusCode >= 400) throw Exception('${r.statusCode}: ${r.body}');
    return json.decode(r.body) as Map<String, dynamic>;
  }

  Future<List<Persona>> personas() async {
    final m = await _get('/api/meta');
    return (m['personas'] as List).map((p) => Persona.fromJson(p)).toList();
  }

  Future<String> createSession(String language, {bool operator = false}) async {
    final r = await _post('/api/session', {'language': language, 'operator_mode': operator});
    return r['id'];
  }

  Future<CaptureResult> capturePersona(String sid, String persona) async =>
      CaptureResult.fromJson(await _post('/api/session/$sid/capture', {'persona': persona}));

  /// Real camera path: post on-device-extracted (and PII-masked) fields.
  Future<CaptureResult> captureDocuments(
          String sid, List<Map<String, dynamic>> documents, String? askedScheme) async =>
      CaptureResult.fromJson(await _post('/api/session/$sid/capture',
          {'documents': documents, if (askedScheme != null) 'asked_scheme': askedScheme}));

  Future<void> resolve(String sid, Map<String, dynamic> resolutions) =>
      _post('/api/session/$sid/resolve', {'resolutions': resolutions});

  Future<void> answer(String sid, Map<String, dynamic> answers) =>
      _post('/api/session/$sid/answer', {'answers': answers});

  Future<Eligibility> eligibility(String sid) async =>
      Eligibility.fromJson(await _get('/api/session/$sid/eligibility'));

  Future<FormFill> selectForm(String sid, String schemeId) async =>
      FormFill.fromJson(await _post('/api/session/$sid/select-form', {'scheme_id': schemeId}));

  Future<TeachBack> teachback(String sid) async =>
      TeachBack.fromJson(await _get('/api/session/$sid/teachback'));

  Future<Output> consent(String sid, {bool confirmed = true, String method = 'voice'}) async =>
      Output.fromJson(
          await _post('/api/session/$sid/consent', {'confirmed': confirmed, 'method': method}));

  Future<void> setReference(String tid, String reference) =>
      _post('/api/tracking/$tid/reference', {'reference_number': reference});

  String fileUrl(String pdfPath) => '$base$pdfPath';
}
