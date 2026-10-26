import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:queueless/main.dart';

void main() {
  testWidgets('QueuelessApp initial smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: QueuelessApp(),
      ),
    );
    // Smoke check that app initializes
    expect(find.byType(QueuelessApp), findsOneWidget);
  });
}
