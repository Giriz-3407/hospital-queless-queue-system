import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/loading_indicator.dart';
import '../../home/models/department_model.dart';

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
  bool _hasExistingTicketError = false;

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
      _hasExistingTicketError = false;
    });

    try {
      final queueRepo = ref.read(queueRepositoryProvider);
      final ticket = await queueRepo.joinQueue(
        departmentId: _selectedDepartmentId!,
        reason: _reasonController.text.trim().isEmpty
            ? null
            : _reasonController.text.trim(),
      );

      // Invalidate relevant providers
      ref.invalidate(myQueuesProvider);
      ref.invalidate(patientSummaryProvider);
      ref.invalidate(departmentsProvider);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Successfully joined queue! Your token is ${ticket.tokenNumber}.',
            ),
            behavior: SnackBarBehavior.floating,
            backgroundColor: AppTheme.completed,
          ),
        );
        // Navigate to the live tracking screen with server-issued ticket ID
        context.go('/queue/${ticket.id}');
      }
    } catch (e) {
      if (mounted) {
        final errText = e.toString().replaceFirst('ApiException: ', '');
        final isAlreadyActive =
            errText.toLowerCase().contains('already hold an active');
        setState(() {
          _isSubmitting = false;
          _errorMessage = errText;
          _hasExistingTicketError = isAlreadyActive;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final departmentsAsync = ref.watch(departmentsProvider);
    final myQueuesAsync = ref.watch(myQueuesProvider);

    // Check if patient already holds an active queue ticket across the hospital
    final activeTickets = myQueuesAsync.value?.where((t) => t.isActive).toList() ?? [];
    final activeTicket = activeTickets.isNotEmpty ? activeTickets.first : null;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Join Virtual Queue'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/home'),
        ),
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
                  'Select a clinical department to take your daily queue token virtually.',
                  style: TextStyle(
                    fontSize: 14,
                    color: AppTheme.textSecondary,
                  ),
                ),
                const SizedBox(height: 20),

                // Policy Restriction Warning if Patient Already Has an Active Ticket
                if (activeTicket != null) ...[
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppTheme.waiting.withAlpha(25),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppTheme.waiting, width: 1.5),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.warning_amber_rounded,
                                color: AppTheme.waiting, size: 26),
                            const SizedBox(width: 10),
                            const Expanded(
                              child: Text(
                                'Active Queue Entry Exists',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                  color: AppTheme.textPrimary,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'You already hold an active queue ticket (${activeTicket.tokenNumber}) in ${activeTicket.departmentName} with status "${activeTicket.status}".\n\n'
                          'Hospital policy permits each patient at most ONE active queue entry across the entire hospital at any time. You may join a new queue only after your current entry reaches a completed or cancelled state.',
                          style: const TextStyle(
                            fontSize: 13,
                            color: AppTheme.textSecondary,
                            height: 1.4,
                          ),
                        ),
                        const SizedBox(height: 14),
                        ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppTheme.accent,
                          ),
                          icon: const Icon(Icons.confirmation_number_outlined,
                              size: 18),
                          label: Text(
                            'View Active Ticket (${activeTicket.tokenNumber})',
                          ),
                          onPressed: () =>
                              context.go('/queue/${activeTicket.id}'),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
                ],

                // Backend Error Banner
                if (_errorMessage != null) ...[
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: AppTheme.error.withAlpha(25),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppTheme.error.withAlpha(60)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Padding(
                              padding: EdgeInsets.only(top: 2),
                              child: Icon(Icons.error_outline,
                                  color: AppTheme.error, size: 20),
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Text(
                                _errorMessage!,
                                style: const TextStyle(
                                  color: AppTheme.error,
                                  fontSize: 13,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ],
                        ),
                        if (_hasExistingTicketError) ...[
                          const SizedBox(height: 12),
                          ElevatedButton.icon(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppTheme.accent,
                              minimumSize: const Size.fromHeight(40),
                            ),
                            icon: const Icon(Icons.confirmation_number_outlined,
                                size: 18),
                            label: const Text('Open My Active Queue'),
                            onPressed: () => context.go('/queue'),
                          ),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
                ],

                // Department Selector
                departmentsAsync.when(
                  data: (departments) {
                    final activeDepts =
                        departments.where((d) => d.isActive).toList();

                    if (activeDepts.isEmpty) {
                      return const Card(
                        child: Padding(
                          padding: EdgeInsets.all(16),
                          child: Text(
                            'No departments are currently accepting queue bookings.',
                            style: TextStyle(color: AppTheme.textSecondary),
                          ),
                        ),
                      );
                    }

                    // Selected department details
                    final selectedDept = activeDepts.cast<DepartmentModel?>().firstWhere(
                          (d) => d?.id == _selectedDepartmentId,
                          orElse: () => null,
                        );

                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        DropdownButtonFormField<String>(
                          initialValue: _selectedDepartmentId,
                          decoration: const InputDecoration(
                            labelText: 'Select Department *',
                            prefixIcon: Icon(Icons.local_hospital_outlined),
                          ),
                          hint: const Text('Choose a department'),
                          items: activeDepts.map((d) {
                            return DropdownMenuItem<String>(
                              value: d.id,
                              child: Text('${d.name} (${d.code})'),
                            );
                          }).toList(),
                          onChanged: activeTicket != null
                              ? null
                              : (val) {
                                  setState(() {
                                    _selectedDepartmentId = val;
                                    _errorMessage = null;
                                  });
                                },
                        ),
                        const SizedBox(height: 16),

                        // Selected Department Info Card
                        if (selectedDept != null) ...[
                          Card(
                            color: AppTheme.primaryLight.withAlpha(50),
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      const Icon(Icons.info_outline,
                                          size: 18, color: AppTheme.primary),
                                      const SizedBox(width: 8),
                                      Expanded(
                                        child: Text(
                                          'Department Summary: ${selectedDept.name}',
                                          style: const TextStyle(
                                            fontWeight: FontWeight.bold,
                                            fontSize: 14,
                                            color: AppTheme.primaryDark,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                  if (selectedDept.description != null &&
                                      selectedDept.description!.isNotEmpty) ...[
                                    const SizedBox(height: 6),
                                    Text(
                                      selectedDept.description!,
                                      style: const TextStyle(
                                        fontSize: 12,
                                        color: AppTheme.textSecondary,
                                      ),
                                    ),
                                  ],
                                  const SizedBox(height: 12),
                                  Row(
                                    mainAxisAlignment:
                                        MainAxisAlignment.spaceBetween,
                                    children: [
                                      Text(
                                        'Waiting Patients: ${selectedDept.currentWaiting}',
                                        style: const TextStyle(
                                          fontSize: 13,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                      Text(
                                        'Est. Wait: ${selectedDept.estimatedWaitMinutes != null ? "~${selectedDept.estimatedWaitMinutes} min" : "Unavailable"}',
                                        style: const TextStyle(
                                          fontSize: 13,
                                          fontWeight: FontWeight.w600,
                                          color: AppTheme.waiting,
                                        ),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(height: 16),
                        ],
                      ],
                    );
                  },
                  loading: () => const LoadingIndicator(
                    message: 'Loading clinical departments...',
                  ),
                  error: (err, _) => Text(
                    'Failed to load departments: $err',
                    style: const TextStyle(color: AppTheme.error),
                  ),
                ),

                // Reason for Visit (Optional)
                TextFormField(
                  controller: _reasonController,
                  enabled: activeTicket == null,
                  maxLines: 3,
                  textInputAction: TextInputAction.done,
                  decoration: const InputDecoration(
                    labelText: 'Reason for Visit (Optional)',
                    hintText: 'e.g. Mild fever, persistent headache, routine checkup',
                    alignLabelWithHint: true,
                    prefixIcon: Padding(
                      padding: EdgeInsets.only(bottom: 40),
                      child: Icon(Icons.notes_rounded),
                    ),
                  ),
                ),
                const SizedBox(height: 28),

                // Submit Button: Disabled if patient already holds active ticket
                ElevatedButton.icon(
                  icon: _isSubmitting
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : Icon(activeTicket != null
                          ? Icons.block_rounded
                          : Icons.check_circle_outline),
                  label: Text(
                    _isSubmitting
                        ? 'Generating Token...'
                        : (activeTicket != null
                            ? 'Already in Active Queue'
                            : 'Confirm & Join Queue'),
                  ),
                  onPressed: (_isSubmitting || activeTicket != null)
                      ? null
                      : _submit,
                ),
                const SizedBox(height: 12),

                OutlinedButton(
                  onPressed: () => context.go('/home'),
                  child: const Text('Back to Home'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
