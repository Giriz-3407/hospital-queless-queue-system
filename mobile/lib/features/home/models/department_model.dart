/// Department model representing hospital clinical departments.
class DepartmentModel {
  final String id;
  final String name;
  final String code;
  final String? description;
  final int avgConsultationTime;
  final bool isActive;
  final int currentWaiting;
  final int? estimatedWaitMinutes;
  final int availableDoctorsCount;
  final int totalDoctorsCount;

  const DepartmentModel({
    required this.id,
    required this.name,
    required this.code,
    this.description,
    this.avgConsultationTime = 15,
    this.isActive = true,
    this.currentWaiting = 0,
    this.estimatedWaitMinutes,
    this.availableDoctorsCount = 0,
    this.totalDoctorsCount = 0,
  });

  factory DepartmentModel.fromJson(Map<String, dynamic> json) {
    return DepartmentModel(
      id: json['id'] as String? ?? json['_id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      code: json['code'] as String? ?? '',
      description: json['description'] as String?,
      avgConsultationTime: json['avg_consultation_time'] as int? ?? 15,
      isActive: json['is_active'] as bool? ?? true,
      currentWaiting: json['current_waiting'] as int? ??
          (json['stats'] is Map ? (json['stats']['waiting'] as int? ?? 0) : 0),
      estimatedWaitMinutes: json['estimated_wait_minutes'] as int?,
      availableDoctorsCount: json['available_doctors_count'] as int? ?? 0,
      totalDoctorsCount: json['total_doctors_count'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'code': code,
        'description': description,
        'avg_consultation_time': avgConsultationTime,
        'is_active': isActive,
        'current_waiting': currentWaiting,
        'estimated_wait_minutes': estimatedWaitMinutes,
        'available_doctors_count': availableDoctorsCount,
        'total_doctors_count': totalDoctorsCount,
      };
}
