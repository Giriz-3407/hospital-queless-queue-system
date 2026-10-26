/// Virtual queue ticket model representing a patient's position in line.
class QueueTicketModel {
  final String id;
  final String departmentId;
  final String departmentName;
  final String departmentCode;
  final String patientId;
  final String patientName;
  final String tokenNumber;
  final String? queueDate;
  final int position;
  final int livePosition;
  final int patientsAhead;
  final int? liveEstimatedWaitMinutes;
  final String status; // WAITING, CALLED, IN_CONSULTATION, COMPLETED, CANCELLED, NO_SHOW
  final String? doctorId;
  final String? doctorName;
  final String? reason;
  final String? notes;
  final String? currentlyServingTicket;
  final String? currentlyCalledTicket;
  final String? joinedAt;
  final String? calledAt;
  final String? completedAt;
  final String? cancelledAt;
  final String? createdAt;

  const QueueTicketModel({
    required this.id,
    required this.departmentId,
    required this.departmentName,
    required this.departmentCode,
    required this.patientId,
    required this.patientName,
    required this.tokenNumber,
    this.queueDate,
    required this.position,
    required this.livePosition,
    required this.patientsAhead,
    this.liveEstimatedWaitMinutes,
    required this.status,
    this.doctorId,
    this.doctorName,
    this.reason,
    this.notes,
    this.currentlyServingTicket,
    this.currentlyCalledTicket,
    this.joinedAt,
    this.calledAt,
    this.completedAt,
    this.cancelledAt,
    this.createdAt,
  });

  bool get isWaiting => status.toUpperCase() == 'WAITING';
  bool get isCalled => status.toUpperCase() == 'CALLED';
  bool get isInConsultation => status.toUpperCase() == 'IN_CONSULTATION';
  bool get isCompleted => status.toUpperCase() == 'COMPLETED';
  bool get isCancelled => status.toUpperCase() == 'CANCELLED';
  bool get isNoShow => status.toUpperCase() == 'NO_SHOW';

  bool get isActive => isWaiting || isCalled || isInConsultation;
  bool get isTerminal => isCompleted || isCancelled || isNoShow;

  factory QueueTicketModel.fromJson(Map<String, dynamic> json) {
    final statusStr = json['status'] as String? ?? 'WAITING';
    final pos = json['position'] as int? ?? 1;
    final livePos = json['live_position'] as int? ?? pos;
    final ahead = json['patients_ahead'] as int? ?? (livePos > 1 ? livePos - 1 : 0);
    final wait = json['live_estimated_wait_minutes'] as int? ??
        json['estimated_wait_minutes'] as int?;

    return QueueTicketModel(
      id: json['id'] as String? ?? json['_id'] as String? ?? '',
      departmentId: json['department_id'] as String? ?? '',
      departmentName: json['department_name'] as String? ?? '',
      departmentCode: json['department_code'] as String? ?? '',
      patientId: json['patient_id'] as String? ?? '',
      patientName: json['patient_name'] as String? ?? '',
      tokenNumber: json['token_number'] as String? ??
          json['ticket_number'] as String? ??
          '',
      queueDate: json['queue_date'] as String?,
      position: pos,
      livePosition: livePos,
      patientsAhead: ahead,
      liveEstimatedWaitMinutes: wait,
      status: statusStr.toUpperCase(),
      doctorId: json['doctor_id'] as String?,
      doctorName: json['doctor_name'] as String?,
      reason: json['reason'] as String?,
      notes: json['notes'] as String?,
      currentlyServingTicket: json['currently_serving_ticket'] as String?,
      currentlyCalledTicket: json['currently_called_ticket'] as String?,
      joinedAt: json['joined_at'] as String?,
      calledAt: json['called_at'] as String?,
      completedAt: json['completed_at'] as String?,
      cancelledAt: json['cancelled_at'] as String?,
      createdAt: json['created_at'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'department_id': departmentId,
        'department_name': departmentName,
        'department_code': departmentCode,
        'patient_id': patientId,
        'patient_name': patientName,
        'token_number': tokenNumber,
        'queue_date': queueDate,
        'position': position,
        'live_position': livePosition,
        'patients_ahead': patientsAhead,
        'live_estimated_wait_minutes': liveEstimatedWaitMinutes,
        'status': status,
        'doctor_id': doctorId,
        'doctor_name': doctorName,
        'reason': reason,
        'notes': notes,
        'currently_serving_ticket': currentlyServingTicket,
        'currently_called_ticket': currentlyCalledTicket,
        'joined_at': joinedAt,
        'called_at': calledAt,
        'completed_at': completedAt,
        'cancelled_at': cancelledAt,
        'created_at': createdAt,
      };
}
