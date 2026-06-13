import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

import '../i18n.dart';
import '../services/ocr.dart';
import '../theme.dart';
import '../widgets.dart';

/// Live camera intake. Each shot is OCR'd ON-DEVICE (ML Kit), PII-masked, and
/// added to a list. Pops back the list of capture-doc payloads for the backend.
class CameraCaptureScreen extends StatefulWidget {
  final String lang;
  const CameraCaptureScreen({super.key, required this.lang});
  @override
  State<CameraCaptureScreen> createState() => _CameraCaptureScreenState();
}

class _CameraCaptureScreenState extends State<CameraCaptureScreen> {
  CameraController? _controller;
  final _ocr = OnDeviceOcr();
  final List<Map<String, dynamic>> _docs = [];
  bool _busy = false;
  String? _hint;

  @override
  void initState() {
    super.initState();
    _initCamera();
  }

  Future<void> _initCamera() async {
    try {
      final cams = await availableCameras();
      final back = cams.firstWhere((c) => c.lensDirection == CameraLensDirection.back,
          orElse: () => cams.first);
      final ctl = CameraController(back, ResolutionPreset.high, enableAudio: false);
      await ctl.initialize();
      if (mounted) setState(() => _controller = ctl);
    } catch (e) {
      if (mounted) setState(() => _hint = 'Camera unavailable: $e');
    }
  }

  Future<void> _shoot() async {
    final ctl = _controller;
    if (ctl == null || _busy) return;
    setState(() { _busy = true; _hint = null; });
    try {
      final shot = await ctl.takePicture();
      final result = await _ocr.readImage(shot.path);
      if (result.recaptureHint != null) {
        setState(() => _hint = result.recaptureHint);
      } else {
        _docs.add(result.toCaptureDoc('cam-${_docs.length}'));
        setState(() => _hint = 'Added ${result.type.replaceAll('_', ' ')} ✓');
      }
    } catch (e) {
      setState(() => _hint = 'Could not read — try again in better light.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    _ocr.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final ready = _controller?.value.isInitialized ?? false;
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black, foregroundColor: Colors.white,
        title: Text(I18n.t('capture', widget.lang)),
      ),
      body: Column(children: [
        Expanded(
          child: Stack(alignment: Alignment.center, children: [
            if (ready) CameraPreview(_controller!) else const ScanFrame(),
            // Framing guides
            IgnorePointer(
              child: Container(
                margin: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  border: Border.all(color: C.saffron.withOpacity(0.8), width: 2),
                  borderRadius: BorderRadius.circular(16)),
              ),
            ),
            if (_hint != null)
              Positioned(
                bottom: 16, left: 16, right: 16,
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.7), borderRadius: BorderRadius.circular(12)),
                  child: Text(_hint!, textAlign: TextAlign.center,
                      style: const TextStyle(color: Colors.white)),
                ),
              ),
          ]),
        ),
        Container(
          color: Colors.black,
          padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
          child: Column(children: [
            Text('${_docs.length} document(s) captured',
                style: const TextStyle(color: Colors.white70)),
            const SizedBox(height: 12),
            Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [
              IconButton.filled(
                onPressed: _busy ? null : _shoot,
                iconSize: 36,
                style: IconButton.styleFrom(backgroundColor: C.saffron, padding: const EdgeInsets.all(20)),
                icon: _busy
                    ? const SizedBox(width: 30, height: 30, child: CircularProgressIndicator(color: Colors.white))
                    : const Icon(Icons.camera_alt, color: Colors.white),
              ),
            ]),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: _docs.isEmpty ? null : () => Navigator.of(context).pop(_docs),
              child: const Text('Done — continue'),
            ),
          ]),
        ),
      ]),
    );
  }
}
