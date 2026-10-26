import '../../../core/config/api_config.dart';
import '../../../core/network/api_client.dart';
import '../models/queue_ticket_model.dart';

/// Repository for patient virtual queue operations.
class QueueRepository {
  final ApiClient _client;

  QueueRepository({ApiClient? client}) : _client = client ?? ApiClient();

  /// Join a virtual queue for a specific hospital department.
  Future<QueueTicketModel> joinQueue({
    required String departmentId,
    String? reason,
  }) async {
    final response = await _client.post<QueueTicketModel>(
      ApiConfig.joinQueueEndpoint,
      data: {
        'department_id': departmentId,
        if (reason != null && reason.trim().isNotEmpty) 'reason': reason.trim(),
      },
      fromDataJson: (data) =>
          QueueTicketModel.fromJson(data as Map<String, dynamic>),
    );
    return response.data!;
  }

  /// Retrieve all tickets belonging to the authenticated patient.
  Future<List<QueueTicketModel>> getMyQueues() async {
    final response = await _client.get<List<QueueTicketModel>>(
      ApiConfig.myQueuesEndpoint,
      fromDataJson: (data) {
        if (data is List) {
          return data
              .map((e) => QueueTicketModel.fromJson(e as Map<String, dynamic>))
              .toList();
        }
        return <QueueTicketModel>[];
      },
    );
    return response.data ?? [];
  }

  /// Retrieve a specific queue ticket by its ID.
  Future<QueueTicketModel> getQueueById(String queueId) async {
    final response = await _client.get<QueueTicketModel>(
      ApiConfig.queueByIdEndpoint(queueId),
      fromDataJson: (data) =>
          QueueTicketModel.fromJson(data as Map<String, dynamic>),
    );
    return response.data!;
  }

  /// Cancel a pending WAITING queue ticket.
  Future<QueueTicketModel> cancelQueue(String queueId) async {
    final response = await _client.post<QueueTicketModel>(
      ApiConfig.cancelQueueEndpoint(queueId),
      fromDataJson: (data) =>
          QueueTicketModel.fromJson(data as Map<String, dynamic>),
    );
    return response.data!;
  }

  /// Retrieve full patient queue history from `/patients/me/queues`.
  Future<List<QueueTicketModel>> getPatientQueueHistory() async {
    final response = await _client.get<List<QueueTicketModel>>(
      ApiConfig.patientQueuesEndpoint,
      fromDataJson: (data) {
        if (data is List) {
          return data
              .map((e) => QueueTicketModel.fromJson(e as Map<String, dynamic>))
              .toList();
        }
        return <QueueTicketModel>[];
      },
    );
    return response.data ?? [];
  }
}
