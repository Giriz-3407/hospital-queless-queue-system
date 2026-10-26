import '../../../core/config/api_config.dart';
import '../../../core/network/api_client.dart';
import '../models/department_model.dart';

/// Repository for clinical departments and live availability.
class DepartmentRepository {
  final ApiClient _client;

  DepartmentRepository({ApiClient? client}) : _client = client ?? ApiClient();

  /// List active departments with queue counts and wait estimates.
  Future<List<DepartmentModel>> getDepartments({bool activeOnly = true}) async {
    final response = await _client.get<List<DepartmentModel>>(
      ApiConfig.departmentsEndpoint,
      queryParameters: activeOnly ? null : {'all': 'true'},
      fromDataJson: (data) {
        if (data is List) {
          return data
              .map((e) => DepartmentModel.fromJson(e as Map<String, dynamic>))
              .toList();
        }
        return <DepartmentModel>[];
      },
    );
    return response.data ?? [];
  }

  /// Retrieve single department details.
  Future<DepartmentModel> getDepartmentById(String departmentId) async {
    final response = await _client.get<DepartmentModel>(
      ApiConfig.departmentByIdEndpoint(departmentId),
      fromDataJson: (data) =>
          DepartmentModel.fromJson(data as Map<String, dynamic>),
    );
    return response.data!;
  }
}
