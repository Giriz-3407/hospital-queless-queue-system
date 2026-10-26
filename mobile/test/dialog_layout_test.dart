import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:queueless/core/theme/app_theme.dart';

void main() {
  testWidgets('Active Queue Policy AlertDialog renders on narrow screens without overflow',
      (WidgetTester tester) async {
    // Simulate narrow mobile screen (320px width)
    tester.view.physicalSize = const Size(320, 640);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.lightTheme,
        home: Scaffold(
          body: Builder(
            builder: (context) => ElevatedButton(
              onPressed: () {
                showDialog(
                  context: context,
                  builder: (ctx) => AlertDialog(
                    title: const Row(
                      children: [
                        Icon(Icons.warning_amber_rounded, color: AppTheme.waiting),
                        SizedBox(width: 10),
                        Expanded(
                          child: Text('Active Queue Policy'),
                        ),
                      ],
                    ),
                    content: const Text(
                      'You already hold an active queue ticket in Cardiology.',
                    ),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.pop(ctx),
                        child: const Text('Close'),
                      ),
                      ElevatedButton(
                        onPressed: () => Navigator.pop(ctx),
                        child: const Text('View Active Ticket'),
                      ),
                    ],
                  ),
                );
              },
              child: const Text('Show Dialog'),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.text('Show Dialog'));
    await tester.pumpAndSettle();

    expect(find.text('Active Queue Policy'), findsOneWidget);
    expect(find.byType(AlertDialog), findsOneWidget);
    // If there is any overflow, Flutter test framework catches it and fails the test.
    expect(tester.takeException(), isNull);
  });
}
