import '../../../core/config/api_config.dart';
import '../../../core/network/api_client.dart';
import '../models/patient_summary_model.dart';

/// Repository for patient dashboard statistics and summary data.
class PatientRepository {
  final ApiClient _client;

  PatientRepository({ApiClient? client}) : _client = client ?? ApiClient();

  /// Fetch authenticated patient profile and queue overview from `/patients/me`.
  Future<PatientSummaryModel> getPatientSummary() async {
    final response = await _client.get<PatientSummaryModel>(
      ApiConfig.patientProfileEndpoint,
      fromDataJson: (data) =>
          PatientSummaryModel.fromJson(data as Map<String, dynamic>),
    );
    return response.data!;
  }
}
