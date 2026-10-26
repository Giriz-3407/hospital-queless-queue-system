import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';

/// Clean status indicator chip matching Queueless queue status codes.
class StatusChip extends StatelessWidget {
  final String status;

  const StatusChip({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    final norm = status.toUpperCase().replaceAll('_', ' ');
    final (bgColor, fgColor) = _getColors(status.toUpperCase());

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        norm,
        style: TextStyle(
          color: fgColor,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  (Color, Color) _getColors(String st) {
    switch (st) {
      case 'WAITING':
        return (AppTheme.waiting.withAlpha(38), AppTheme.waiting);
      case 'CALLED':
        return (AppTheme.called.withAlpha(38), AppTheme.called);
      case 'IN_CONSULTATION':
        return (AppTheme.inConsultation.withAlpha(38), AppTheme.inConsultation);
      case 'COMPLETED':
        return (AppTheme.completed.withAlpha(38), AppTheme.completed);
      case 'CANCELLED':
      case 'NO_SHOW':
      default:
        return (AppTheme.cancelled.withAlpha(38), AppTheme.cancelled);
    }
  }
}
