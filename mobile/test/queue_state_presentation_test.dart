import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:queueless/features/queue/models/queue_ticket_model.dart';
import 'package:queueless/shared/widgets/status_chip.dart';

void main() {
  group('Queue State Presentation and Status Chips', () {
    testWidgets('StatusChip renders WAITING status correctly', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: StatusChip(status: 'WAITING'),
          ),
        ),
      );

      expect(find.text('WAITING'), findsOneWidget);
    });

    testWidgets('StatusChip renders CALLED status with Sky color', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: StatusChip(status: 'CALLED'),
          ),
        ),
      );

      expect(find.text('CALLED'), findsOneWidget);
    });

    testWidgets('StatusChip renders IN_CONSULTATION status with Consultation label', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: StatusChip(status: 'IN_CONSULTATION'),
          ),
        ),
      );

      expect(find.text('IN CONSULTATION'), findsOneWidget);
    });

    testWidgets('StatusChip renders COMPLETED status', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: StatusChip(status: 'COMPLETED'),
          ),
        ),
      );

      expect(find.text('COMPLETED'), findsOneWidget);
    });

    test('Queue ticket correctly differentiates active and terminal states', () {
      QueueTicketModel createWithStatus(String status) {
        return QueueTicketModel(
          id: '1',
          departmentId: 'd',
          departmentName: 'Dentistry',
          departmentCode: 'DENT',
          patientId: 'p',
          patientName: 'Jane',
          tokenNumber: 'DENT-001',
          position: 1,
          livePosition: 1,
          patientsAhead: 0,
          status: status,
        );
      }

      final waitingTicket = createWithStatus('WAITING');
      expect(waitingTicket.isActive, isTrue);
      expect(waitingTicket.isTerminal, isFalse);
      expect(waitingTicket.isWaiting, isTrue);

      final calledTicket = createWithStatus('CALLED');
      expect(calledTicket.isActive, isTrue);
      expect(calledTicket.isTerminal, isFalse);
      expect(calledTicket.isCalled, isTrue);

      final consultationTicket = createWithStatus('IN_CONSULTATION');
      expect(consultationTicket.isActive, isTrue);
      expect(consultationTicket.isTerminal, isFalse);
      expect(consultationTicket.isInConsultation, isTrue);

      final completedTicket = createWithStatus('COMPLETED');
      expect(completedTicket.isActive, isFalse);
      expect(completedTicket.isTerminal, isTrue);
      expect(completedTicket.isCompleted, isTrue);

      final cancelledTicket = createWithStatus('CANCELLED');
      expect(cancelledTicket.isActive, isFalse);
      expect(cancelledTicket.isTerminal, isTrue);
      expect(cancelledTicket.isCancelled, isTrue);

      final noShowTicket = createWithStatus('NO_SHOW');
      expect(noShowTicket.isActive, isFalse);
      expect(noShowTicket.isTerminal, isTrue);
      expect(noShowTicket.isNoShow, isTrue);
    });

    test('Single active queue entry rule correctly gates queue eligibility', () {
      bool canJoinNewQueue(List<QueueTicketModel> tickets) {
        return !tickets.any((t) => t.isActive);
      }

      QueueTicketModel create(String status) => QueueTicketModel(
            id: '1',
            departmentId: 'd',
            departmentName: 'D',
            departmentCode: 'D',
            patientId: 'p',
            patientName: 'P',
            tokenNumber: 'D-001',
            position: 1,
            livePosition: 1,
            patientsAhead: 0,
            status: status,
          );

      // Patient with active WAITING ticket cannot join
      expect(canJoinNewQueue([create('WAITING')]), isFalse);

      // Patient with active CALLED ticket cannot join
      expect(canJoinNewQueue([create('CALLED')]), isFalse);

      // Patient with active IN_CONSULTATION ticket cannot join
      expect(canJoinNewQueue([create('IN_CONSULTATION')]), isFalse);

      // Patient with only CANCELLED ticket CAN join
      expect(canJoinNewQueue([create('CANCELLED')]), isTrue);

      // Patient with only COMPLETED ticket CAN join
      expect(canJoinNewQueue([create('COMPLETED')]), isTrue);

      // Patient with only NO_SHOW ticket CAN join
      expect(canJoinNewQueue([create('NO_SHOW')]), isTrue);

      // Patient with 2 completed tickets and 1 active ticket cannot join
      expect(
        canJoinNewQueue([create('COMPLETED'), create('COMPLETED'), create('WAITING')]),
        isFalse,
      );

      // Patient with no previous tickets can join
      expect(canJoinNewQueue([]), isTrue);
    });
  });
}
