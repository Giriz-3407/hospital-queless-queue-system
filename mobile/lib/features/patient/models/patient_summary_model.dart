import '../../auth/models/user_model.dart';
import '../../queue/models/queue_ticket_model.dart';

/// Patient summary data returned from `/api/v1/patients/me`.
class PatientSummaryModel {
  final UserModel profile;
  final int activeTicketsCount;
  final int pastVisitsCount;
  final List<QueueTicketModel> activeQueues;
  final List<QueueTicketModel> recentQueues;

  const PatientSummaryModel({
    required this.profile,
    required this.activeTicketsCount,
    required this.pastVisitsCount,
    required this.activeQueues,
    required this.recentQueues,
  });

  factory PatientSummaryModel.fromJson(Map<String, dynamic> json) {
    final profileJson = json['profile'] as Map<String, dynamic>? ?? {};
    final summaryJson = json['summary'] as Map<String, dynamic>? ?? {};
    final activeList = json['active_queues'] as List? ?? [];
    final recentList = json['recent_queues'] as List? ?? [];

    return PatientSummaryModel(
      profile: UserModel.fromJson(profileJson),
      activeTicketsCount: summaryJson['active_tickets_count'] as int? ?? 0,
      pastVisitsCount: summaryJson['past_visits_count'] as int? ?? 0,
      activeQueues: activeList
          .map((e) => QueueTicketModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      recentQueues: recentList
          .map((e) => QueueTicketModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}
