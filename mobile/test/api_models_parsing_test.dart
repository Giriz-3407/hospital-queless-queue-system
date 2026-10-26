import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:queueless/core/network/api_exception.dart';
import 'package:queueless/core/network/api_response.dart';
import 'package:queueless/features/auth/models/user_model.dart';
import 'package:queueless/features/home/models/department_model.dart';
import 'package:queueless/features/patient/models/patient_summary_model.dart';
import 'package:queueless/features/queue/models/queue_ticket_model.dart';

void main() {
  group('API Models Parsing Tests', () {
    test('UserModel parses backend JSON document correctly', () {
      final json = {
        'id': '6adfa899d2bf211a297e0fcf',
        'name': 'Jane Doe',
        'email': 'jane.doe@example.com',
        'phone': '+1-555-0199',
        'role': 'patient',
        'is_active': true,
        'created_at': '2026-10-27T00:00:00+00:00',
      };

      final user = UserModel.fromJson(json);

      expect(user.id, '6adfa899d2bf211a297e0fcf');
      expect(user.name, 'Jane Doe');
      expect(user.email, 'jane.doe@example.com');
      expect(user.phone, '+1-555-0199');
      expect(user.role, 'patient');
      expect(user.isActive, isTrue);
      expect(user.createdAt, isNotNull);
    });

    test('DepartmentModel parses live queue metrics and assigned doctors', () {
      final json = {
        'id': 'dept123',
        'name': 'General Medicine',
        'code': 'GEN',
        'description': 'Outpatient primary medical care',
        'avg_consultation_time': 15,
        'is_active': true,
        'current_waiting': 4,
        'estimated_wait_minutes': 30,
        'available_doctors_count': 2,
        'total_doctors_count': 3,
      };

      final dept = DepartmentModel.fromJson(json);

      expect(dept.id, 'dept123');
      expect(dept.name, 'General Medicine');
      expect(dept.code, 'GEN');
      expect(dept.currentWaiting, 4);
      expect(dept.estimatedWaitMinutes, 30);
      expect(dept.availableDoctorsCount, 2);
      expect(dept.totalDoctorsCount, 3);
    });

    test('QueueTicketModel parses live queue position and status flags', () {
      final json = {
        'id': 'ticket456',
        'department_id': 'dept123',
        'department_name': 'Pediatrics',
        'department_code': 'PED',
        'patient_id': 'pat789',
        'patient_name': 'Jane Doe',
        'token_number': 'PED-003',
        'queue_date': '2026-10-27',
        'position': 3,
        'live_position': 2,
        'patients_ahead': 1,
        'live_estimated_wait_minutes': 15,
        'status': 'WAITING',
        'doctor_name': 'Dr. Sarah Smith',
        'reason': 'Checkup',
        'currently_serving_ticket': 'PED-001',
        'currently_called_ticket': 'PED-002',
        'joined_at': '2026-10-27T08:30:00Z',
      };

      final ticket = QueueTicketModel.fromJson(json);

      expect(ticket.id, 'ticket456');
      expect(ticket.tokenNumber, 'PED-003');
      expect(ticket.position, 3);
      expect(ticket.livePosition, 2);
      expect(ticket.patientsAhead, 1);
      expect(ticket.liveEstimatedWaitMinutes, 15);
      expect(ticket.status, 'WAITING');
      expect(ticket.isWaiting, isTrue);
      expect(ticket.isActive, isTrue);
      expect(ticket.isTerminal, isFalse);
      expect(ticket.currentlyServingTicket, 'PED-001');
      expect(ticket.currentlyCalledTicket, 'PED-002');
    });

    test('PatientSummaryModel parses summary stats and visit collections', () {
      final json = {
        'profile': {
          'id': 'pat1',
          'name': 'John Smith',
          'email': 'john@test.com',
          'role': 'patient',
        },
        'summary': {
          'active_tickets_count': 1,
          'past_visits_count': 5,
        },
        'active_queues': [
          {
            'id': 't1',
            'department_id': 'd1',
            'department_name': 'Cardiology',
            'department_code': 'CARD',
            'patient_id': 'pat1',
            'patient_name': 'John Smith',
            'token_number': 'CARD-001',
            'status': 'WAITING',
            'position': 1,
          }
        ],
        'recent_queues': [],
      };

      final summary = PatientSummaryModel.fromJson(json);

      expect(summary.profile.name, 'John Smith');
      expect(summary.activeTicketsCount, 1);
      expect(summary.pastVisitsCount, 5);
      expect(summary.activeQueues.length, 1);
      expect(summary.activeQueues.first.tokenNumber, 'CARD-001');
      expect(summary.recentQueues, isEmpty);
    });

    test('ApiResponse parses standardized success envelope', () {
      final json = {
        'success': true,
        'message': 'Operation successful',
        'data': {'key': 'value'},
        'timestamp': '2026-10-27T00:00:00Z',
      };

      final response = ApiResponse.fromJson(
        json,
        (data) => (data as Map)['key'] as String,
      );

      expect(response.success, isTrue);
      expect(response.message, 'Operation successful');
      expect(response.data, 'value');
      expect(response.timestamp, isNotNull);
    });

    test('ApiException extracts backend standardized error envelopes', () {
      final dioException = DioException(
        requestOptions: RequestOptions(path: '/api/v1/queues/join'),
        response: Response(
          requestOptions: RequestOptions(path: '/api/v1/queues/join'),
          statusCode: 400,
          data: {
            'success': false,
            'error': {
              'code': 'ACTIVE_QUEUE_EXISTS',
              'message': 'You already hold an active queue ticket in Cardiology.',
              'details': null,
            },
            'timestamp': '2026-10-27T00:00:00Z',
          },
        ),
      );

      final apiException = ApiException.fromDioException(dioException);

      expect(apiException.statusCode, 400);
      expect(apiException.code, 'ACTIVE_QUEUE_EXISTS');
      expect(
        apiException.message,
        'You already hold an active queue ticket in Cardiology.',
      );
    });

    test('ApiException formats connection error clearly for patient UI', () {
      final connectionError = DioException(
        requestOptions: RequestOptions(path: '/api/v1/health'),
        type: DioExceptionType.connectionError,
      );

      final apiException = ApiException.fromDioException(connectionError);

      expect(apiException.code, 'CONNECTION_ERROR');
      expect(apiException.message, contains('Unable to connect to the hospital server'));
    });
  });
}
