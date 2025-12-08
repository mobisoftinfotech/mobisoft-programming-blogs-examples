import 'package:biometrics_poc/helpers/biometric_helper.dart';
import 'package:flutter/material.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _biometricHelper = BiometricHelper();
  bool _isDeviceCapable = false;
  bool _isBiometricEnabled = false;
  bool _isAuthenticating = false;
  bool _isLoading = true;
  String? _biometricType;

  @override
  void initState() {
    super.initState();
    _checkBiometricStatus();
  }

  Future<void> _checkBiometricStatus() async {
    final isCapable = await _biometricHelper.isDeviceCapable();
    final isEnabled = await _biometricHelper.isBiometricEnabled();
    final biometricType = await _biometricHelper.getBiometricType();
    setState(() {
      _isDeviceCapable = isCapable;
      _isBiometricEnabled = isEnabled;
      _biometricType = biometricType;
      _isLoading = false;
    });
  }

  Future<void> _handleBiometricLogin() async {
    setState(() {
      _isAuthenticating = true;
    });

    final result = await _biometricHelper.authenticate('Authenticate to login');

    setState(() {
      _isAuthenticating = false;
    });

    if (result && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Biometric authentication successful')),
      );
    } else if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Biometric authentication failed')),
      );
    }
  }

  String _getErrorMessage() {
    if (!_isDeviceCapable) {
      return 'Device is not capable of biometric authentication';
    }
    if (!_isBiometricEnabled) {
      return 'Biometric authentication is not enabled on this device';
    }
    return '';
  }

  @override
  Widget build(BuildContext context) {
    final canUseBiometric = _isDeviceCapable && _isBiometricEnabled;

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Biometric Auth',
                style: TextStyle(
                  fontSize: 32,
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 48),
              if (_isLoading)
                const Center(child: CircularProgressIndicator())
              else if (canUseBiometric)
                ElevatedButton(
                  onPressed: _isAuthenticating ? null : _handleBiometricLogin,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                      child: _isAuthenticating
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : Text(_biometricType != null 
                          ? 'Use $_biometricType for Authentication'
                          : 'Use Biometric for Authentication'),
                )
              else
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.orange.shade50,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.orange.shade200),
                  ),
                  child: Text(
                    _getErrorMessage(),
                    style: const TextStyle(color: Colors.orange),
                    textAlign: TextAlign.center,
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
