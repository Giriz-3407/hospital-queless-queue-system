import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/providers.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/loading_indicator.dart';
import '../../../shared/widgets/status_chip.dart';
import '../../queue/models/queue_ticket_model.dart';

final singleTicketProvider =
    FutureProvider.autoDispose.family<QueueTicketModel, String>((ref, id) async {
  final repo = ref.watch(queueRepositoryProvider);
  return repo.getQueueById(id);
});

class QueueStatusScreen extends ConsumerStatefulWidget {
  final String queueId;

  const QueueStatusScreen({super.key, required this.queueId});

  @override
  ConsumerState<QueueStatusScreen> createState() => _QueueStatusScreenState();
}

class _QueueStatusScreenState extends ConsumerState<QueueStatusScreen> {
  bool _isCancelling = false;
  String? _actionError;

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
            child: const Text('Yes, Cancel'),
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
      await repo.cancelQueue(widget.queueId);
      ref.invalidate(singleTicketProvider(widget.queueId));
      ref.invalidate(myQueuesProvider);
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

  @override
  Widget build(BuildContext context) {
    final ticketAsync = ref.watch(singleTicketProvider(widget.queueId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Live Queue Ticket'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Refresh Status',
            onPressed: () =>
                ref.invalidate(singleTicketProvider(widget.queueId)),
          ),
        ],
      ),
      body: ticketAsync.when(
        data: (ticket) => SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Ticket Header Card
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                ticket.departmentName,
                                style: const TextStyle(
                                  fontSize: 16,
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
                          StatusChip(status: ticket.status),
                        ],
                      ),
                      const SizedBox(height: 24),
                      // Big Ticket Token
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(vertical: 20),
                        decoration: BoxDecoration(
                          color: AppTheme.primaryLight.withAlpha(128),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(
                            color: AppTheme.primary.withAlpha(50),
                          ),
                        ),
                        child: Column(
                          children: [
                            const Text(
                              'YOUR TOKEN NUMBER',
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w700,
                                letterSpacing: 1.2,
                                color: AppTheme.primaryDark,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              ticket.tokenNumber,
                              style: const TextStyle(
                                fontSize: 40,
                                fontWeight: FontWeight.w900,
                                letterSpacing: 2,
                                color: AppTheme.primaryDark,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 20),

                      // Urgent Callout if CALLED
                      if (ticket.isCalled) ...[
                        Container(
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: AppTheme.called.withAlpha(25),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: AppTheme.called),
                          ),
                          child: const Row(
                            children: [
                              Icon(Icons.campaign_rounded,
                                  color: AppTheme.called, size: 28),
                              SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  'Your turn has been called! Please proceed to the consultation room immediately.',
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    color: AppTheme.called,
                                    fontSize: 13,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),
                      ],

                      // Grid of Position, Wait, Patients Ahead
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          _DetailMetric(
                            label: 'Queue Position',
                            value: ticket.isActive
                                ? '#${ticket.livePosition}'
                                : '--',
                            color: AppTheme.accent,
                          ),
                          _DetailMetric(
                            label: 'Patients Ahead',
                            value: ticket.isActive
                                ? '${ticket.patientsAhead}'
                                : '--',
                            color: AppTheme.textPrimary,
                          ),
                          _DetailMetric(
                            label: 'Est. Wait Time',
                            value: ticket.isActive
                                ? (ticket.liveEstimatedWaitMinutes != null
                                    ? '${ticket.liveEstimatedWaitMinutes} min'
                                    : '--')
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

              // Currently Serving Card
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      const Icon(Icons.info_outline,
                          color: AppTheme.accent, size: 22),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Clinic Status',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                              ),
                            ),
                            Text(
                              ticket.currentlyServingTicket != null
                                  ? 'Currently Serving: ${ticket.currentlyServingTicket}'
                                  : 'No patient currently being served',
                              style: const TextStyle(
                                fontSize: 13,
                                color: AppTheme.textSecondary,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Error banner if cancel failed
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

              // Cancel button (only allowed for WAITING tickets)
              if (ticket.isWaiting) ...[
                OutlinedButton.icon(
                  icon: _isCancelling
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.cancel_outlined,
                          color: AppTheme.error),
                  label: Text(
                    _isCancelling ? 'Cancelling...' : 'Cancel Ticket',
                    style: const TextStyle(color: AppTheme.error),
                  ),
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: AppTheme.error),
                  ),
                  onPressed: _isCancelling ? null : _cancelTicket,
                ),
                const SizedBox(height: 12),
              ],

              // Back to Home
              TextButton.icon(
                icon: const Icon(Icons.arrow_back),
                label: const Text('Back to Home'),
                onPressed: () => context.go('/home'),
              ),
            ],
          ),
        ),
        loading: () => const LoadingIndicator(
          message: 'Fetching live ticket status...',
        ),
        error: (err, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.error_outline,
                    color: AppTheme.error, size: 36),
                const SizedBox(height: 8),
                Text(
                  'Failed to load ticket:\n$err',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: AppTheme.error),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () =>
                      ref.invalidate(singleTicketProvider(widget.queueId)),
                  child: const Text('Retry'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _DetailMetric extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _DetailMetric({
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
