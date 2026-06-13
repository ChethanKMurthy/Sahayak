// Minimal smoke test: a basic scaffold builds.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('App scaffold builds', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: Scaffold(body: Text('Sahayak'))));
    expect(find.text('Sahayak'), findsOneWidget);
  });
}
