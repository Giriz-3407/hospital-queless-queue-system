import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/loading_indicator.dart';

class JoinQueueScreen extends ConsumerStatefulWidget {
  final String? initialDeptId;
  final String? initialDeptName;

  const JoinQueueScreen({
    super.key,
    this.initialDeptId,
    this.initialDeptName,
  });

  @override
  ConsumerState<JoinQueueScreen> createState() => _JoinQueueScreenState();
}

class _JoinQueueScreenState extends ConsumerState<JoinQueueScreen> {
  final _formKey = GlobalKey<FormState>();
  String? _selectedDepartmentId;
  final _reasonController = TextEditingController();
  bool _isSubmitting = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _selectedDepartmentId = widget.initialDeptId;
  }

  @override
  void dispose() {
    _reasonController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_selectedDepartmentId == null || _selectedDepartmentId!.isEmpty) {
      setState(() => _errorMessage = 'Please select a hospital department');
      return;
    }

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });

    try {
      final queueRepo = ref.read(queueRepositoryProvider);
      final ticket = await queueRepo.joinQueue(
        departmentId: _selectedDepartmentId!,
        reason: _reasonController.text.trim().isEmpty
            ? null
            : _reasonController.text.trim(),
      );

      // Invalidate queues provider so home screen updates
      ref.invalidate(myQueuesProvider);

      if (mounted) {
        context.go('/queue/${ticket.id}');
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
          _errorMessage = e.toString().replaceFirst('ApiException: ', '');
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final departmentsAsync = ref.watch(departmentsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Join Virtual Queue'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Book Your Place in Line',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.textPrimary,
                  ),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Choose a clinical department and receive your virtual queue ticket instantly.',
                  style: TextStyle(
                    fontSize: 14,
                    color: AppTheme.textSecondary,
                  ),
                ),
                const SizedBox(height: 24),

                // Error message banner
                if (_errorMessage != null) ...[
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppTheme.error.withAlpha(25),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppTheme.error.withAlpha(50)),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.error_outline,
                            color: AppTheme.error, size: 20),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            _errorMessage!,
                            style: const TextStyle(
                                color: AppTheme.error, fontSize: 13),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
                ],

                // Department Selector
                departmentsAsync.when(
                  data: (departments) {
                    if (departments.isEmpty) {
                      return const Text('No active departments found.');
                    }
                    return DropdownButtonFormField<String>(
                      initialValue: _selectedDepartmentId,
                      decoration: const InputDecoration(
                        labelText: 'Select Department *',
                        prefixIcon: Icon(Icons.local_hospital_outlined),
                      ),
                      items: departments.map((d) {
                        return DropdownMenuItem<String>(
                          value: d.id,
                          child: Text('${d.name} (${d.code})'),
                        );
                      }).toList(),
                      onChanged: (val) {
                        setState(() => _selectedDepartmentId = val);
                      },
                      validator: (val) =>
                          val == null ? 'Please select a department' : null,
                    );
                  },
                  loading: () => const LoadingIndicator(
                    message: 'Loading hospital departments...',
                  ),
                  error: (e, _) => Text(
                    'Failed to load departments: $e',
                    style: const TextStyle(color: AppTheme.error),
                  ),
                ),
                const SizedBox(height: 18),

                // Reason / Symptoms
                TextFormField(
                  controller: _reasonController,
                  maxLines: 3,
                  decoration: const InputDecoration(
                    labelText: 'Reason for Visit / Symptoms (Optional)',
                    hintText: 'e.g. Mild headache, routine consultation...',
                    alignLabelWithHint: true,
                  ),
                ),
                const SizedBox(height: 28),

                // Submit Button
                ElevatedButton(
                  onPressed: _isSubmitting ? null : _submit,
                  child: _isSubmitting
                      ? const SizedBox(
                          width: 22,
                          height: 22,
                          child: CircularProgressIndicator(
                            strokeWidth: 2.5,
                            color: Colors.white,
                          ),
                        )
                      : const Text('Get Queue Ticket'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
