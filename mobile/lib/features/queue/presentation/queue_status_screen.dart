import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/loading_indicator.dart';
import '../../../shared/widgets/status_chip.dart';
import '../models/queue_ticket_model.dart';

final singleTicketProvider =
    FutureProvider.autoDispose.family<QueueTicketModel, String>((ref, id) async {
  final repo = ref.watch(queueRepositoryProvider);
  return repo.getQueueById(id);
});

/// Live queue tracking screen with auto-polling (every 10s), background pausing,
/// foreground instant refresh, and ticket cancellation.
class QueueStatusScreen extends ConsumerStatefulWidget {
  final String queueId;

  const QueueStatusScreen({super.key, required this.queueId});

  @override
  ConsumerState<QueueStatusScreen> createState() => _QueueStatusScreenState();
}

class _QueueStatusScreenState extends ConsumerState<QueueStatusScreen>
    with WidgetsBindingObserver {
  Timer? _pollingTimer;
  bool _isPollingInProgress = false;
  bool _isCancelling = false;
  String? _actionError;
  QueueTicketModel? _lastKnownTicket;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _startPolling();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _stopPolling();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      // App foregrounded: trigger immediate refresh and ensure timer running
      _pollTicket();
      _startPolling();
    } else if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.inactive) {
      // App backgrounded: pause polling
      _stopPolling();
    }
  }

  void _startPolling() {
    _pollingTimer?.cancel();
    // Poll every 10 seconds while screen is visible
    _pollingTimer = Timer.periodic(const Duration(seconds: 10), (_) {
      _pollTicket();
    });
  }

  void _stopPolling() {
    _pollingTimer?.cancel();
    _pollingTimer = null;
  }

  Future<void> _pollTicket() async {
    if (_isPollingInProgress || !mounted) return;
    _isPollingInProgress = true;

    try {
      final repo = ref.read(queueRepositoryProvider);
      final updated = await repo.getQueueById(widget.queueId);
      if (mounted) {
        setState(() {
          _lastKnownTicket = updated;
        });
        // Invalidate provider so any Riverpod listeners update smoothly
        ref.invalidate(singleTicketProvider(widget.queueId));

        // Stop polling if ticket reached terminal state
        if (updated.isTerminal) {
          _stopPolling();
        }
      }
    } catch (_) {
      // Silently keep last known ticket during temporary polling connectivity drops
    } finally {
      _isPollingInProgress = false;
    }
  }

  Future<void> _cancelTicket() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Cancel Queue Ticket?'),
        content: const Text(
          'Are you sure you want to cancel your place in this virtual queue? This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Keep Ticket'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.error,
              foregroundColor: Colors.white,
            ),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Yes, Cancel Ticket'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    setState(() {
      _isCancelling = true;
      _actionError = null;
    });

    try {
      final repo = ref.read(queueRepositoryProvider);
      final cancelled = await repo.cancelQueue(widget.queueId);
      _stopPolling();
      if (mounted) {
        setState(() {
          _lastKnownTicket = cancelled;
        });
        ref.invalidate(singleTicketProvider(widget.queueId));
        ref.invalidate(myQueuesProvider);
        ref.invalidate(patientSummaryProvider);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Your queue ticket has been cancelled.'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _actionError = e.toString().replaceFirst('ApiException: ', '');
        });
      }
    } finally {
      if (mounted) {
        setState(() => _isCancelling = false);
      }
    }
  }

  String _formatDateTime(String? isoString) {
    if (isoString == null || isoString.isEmpty) return '--';
    try {
      final dt = DateTime.parse(isoString).toLocal();
      return DateFormat('MMM dd, yyyy • hh:mm a').format(dt);
    } catch (_) {
      return isoString;
    }
  }

  @override
  Widget build(BuildContext context) {
    final ticketAsync = ref.watch(singleTicketProvider(widget.queueId));

    void handleBack() {
      if (context.canPop()) {
        context.pop();
      } else {
        context.go('/home');
      }
    }

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) {
        if (didPop) return;
        handleBack();
      },
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Live Queue Tracking'),
          leading: IconButton(
            icon: const Icon(Icons.arrow_back),
            onPressed: handleBack,
          ),
        actions: [
          if (_isPollingInProgress)
            const Center(
              child: Padding(
                padding: EdgeInsets.symmetric(horizontal: 16),
                child: SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: AppTheme.primary,
                  ),
                ),
              ),
            )
          else
            IconButton(
              icon: const Icon(Icons.refresh_rounded),
              tooltip: 'Refresh Status',
              onPressed: _pollTicket,
            ),
        ],
      ),
      body: ticketAsync.when(
        data: (ticket) {
          _lastKnownTicket = ticket;
          if (ticket.isTerminal) {
            _stopPolling();
          }
          return _buildTicketView(ticket);
        },
        loading: () => _lastKnownTicket != null
            ? _buildTicketView(_lastKnownTicket!)
            : const LoadingIndicator(message: 'Fetching live ticket status...'),
        error: (err, _) => _lastKnownTicket != null
            ? _buildTicketView(_lastKnownTicket!)
            : Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.error_outline,
                          color: AppTheme.error, size: 40),
                      const SizedBox(height: 12),
                      Text(
                        'Failed to load queue ticket:\n$err',
                        textAlign: TextAlign.center,
                        style: const TextStyle(color: AppTheme.error),
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _pollTicket,
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                ),
              ),
      ),
    ),
  );
}

  Widget _buildTicketView(QueueTicketModel ticket) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Status Callout Banner
          if (ticket.isCalled) ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.called.withAlpha(25),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppTheme.called, width: 1.5),
              ),
              child: const Row(
                children: [
                  Icon(Icons.campaign_rounded,
                      color: AppTheme.called, size: 32),
                  SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'YOUR TURN IS CALLED!',
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w900,
                            color: AppTheme.called,
                            letterSpacing: 0.5,
                          ),
                        ),
                        SizedBox(height: 2),
                        Text(
                          'Please proceed immediately to the consultation room.',
                          style: TextStyle(
                            fontSize: 13,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ] else if (ticket.isInConsultation) ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.inConsultation.withAlpha(25),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppTheme.inConsultation, width: 1.5),
              ),
              child: const Row(
                children: [
                  Icon(Icons.health_and_safety_outlined,
                      color: AppTheme.inConsultation, size: 32),
                  SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'IN CONSULTATION',
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w900,
                            color: AppTheme.inConsultation,
                            letterSpacing: 0.5,
                          ),
                        ),
                        SizedBox(height: 2),
                        Text(
                          'Your consultation with the physician is currently in progress.',
                          style: TextStyle(
                            fontSize: 13,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ] else if (ticket.isCompleted) ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.completed.withAlpha(25),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppTheme.completed, width: 1.5),
              ),
              child: const Row(
                children: [
                  Icon(Icons.check_circle_outline,
                      color: AppTheme.completed, size: 32),
                  SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'CONSULTATION COMPLETED',
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w900,
                            color: AppTheme.completed,
                          ),
                        ),
                        SizedBox(height: 2),
                        Text(
                          'Thank you for visiting. Your record is saved in history.',
                          style: TextStyle(
                            fontSize: 13,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],

          // Main Ticket Card
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              ticket.departmentName,
                              style: const TextStyle(
                                fontSize: 17,
                                fontWeight: FontWeight.bold,
                                color: AppTheme.textPrimary,
                              ),
                            ),
                            Text(
                              'Department Code: ${ticket.departmentCode}',
                              style: const TextStyle(
                                fontSize: 12,
                                color: AppTheme.textSecondary,
                              ),
                            ),
                          ],
                        ),
                      ),
                      StatusChip(status: ticket.status),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // Large Token Callout
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(vertical: 20),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryLight.withAlpha(128),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(
                        color: AppTheme.primary.withAlpha(60),
                      ),
                    ),
                    child: Column(
                      children: [
                        const Text(
                          'TOKEN NUMBER',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 1.2,
                            color: AppTheme.primaryDark,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          ticket.tokenNumber,
                          style: const TextStyle(
                            fontSize: 42,
                            fontWeight: FontWeight.w900,
                            letterSpacing: 2,
                            color: AppTheme.primaryDark,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Live Position Metrics Row
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _MetricItem(
                        label: 'Queue Position',
                        value: ticket.isActive
                            ? '#${ticket.livePosition}'
                            : '--',
                        color: AppTheme.accent,
                      ),
                      _MetricItem(
                        label: 'Patients Ahead',
                        value: ticket.isActive
                            ? '${ticket.patientsAhead}'
                            : '--',
                        color: AppTheme.textPrimary,
                      ),
                      _MetricItem(
                        label: 'Est. Wait Time',
                        value: ticket.isActive
                            ? (ticket.liveEstimatedWaitMinutes != null
                                ? '~${ticket.liveEstimatedWaitMinutes} min'
                                : 'Unavailable')
                            : '--',
                        color: AppTheme.waiting,
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Clinic Progress Card
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Department Live Counter',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      const Icon(Icons.record_voice_over_outlined,
                          size: 18, color: AppTheme.accent),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Currently Called: ${ticket.currentlyCalledTicket ?? "None"}',
                          style: const TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      const Icon(Icons.medical_services_outlined,
                          size: 18, color: AppTheme.primary),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Currently Serving: ${ticket.currentlyServingTicket ?? "None"}',
                          style: const TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Ticket Details Card
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Ticket Details',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 12),
                  _DetailRow(
                    label: 'Joined At',
                    value: _formatDateTime(ticket.joinedAt ?? ticket.createdAt),
                  ),
                  if (ticket.doctorName != null) ...[
                    const SizedBox(height: 8),
                    _DetailRow(
                      label: 'Attending Doctor',
                      value: ticket.doctorName!,
                    ),
                  ],
                  if (ticket.reason != null && ticket.reason!.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    _DetailRow(
                      label: 'Reason for Visit',
                      value: ticket.reason!,
                    ),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),

          // Action Error Banner
          if (_actionError != null) ...[
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.error.withAlpha(25),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.error.withAlpha(50)),
              ),
              child: Text(
                _actionError!,
                style: const TextStyle(color: AppTheme.error, fontSize: 13),
              ),
            ),
            const SizedBox(height: 16),
          ],

          // Cancel Action (only if ticket is WAITING)
          if (ticket.isWaiting) ...[
            OutlinedButton.icon(
              icon: _isCancelling
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.cancel_outlined, color: AppTheme.error),
              label: Text(
                _isCancelling ? 'Cancelling Ticket...' : 'Cancel Queue Ticket',
                style: const TextStyle(color: AppTheme.error),
              ),
              style: OutlinedButton.styleFrom(
                side: const BorderSide(color: AppTheme.error),
              ),
              onPressed: _isCancelling ? null : _cancelTicket,
            ),
            const SizedBox(height: 12),
          ],

          // Back to Dashboard
          TextButton.icon(
            icon: const Icon(Icons.home_outlined),
            label: const Text('Back to Home Dashboard'),
            onPressed: () => context.go('/home'),
          ),
        ],
      ),
    );
  }
}

class _MetricItem extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _MetricItem({
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          label,
          style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w800,
            color: color,
          ),
        ),
      ],
    );
  }
}

class _DetailRow extends StatelessWidget {
  final String label;
  final String value;

  const _DetailRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 120,
          child: Text(
            label,
            style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary),
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: AppTheme.textPrimary,
            ),
          ),
        ),
      ],
    );
  }
}
