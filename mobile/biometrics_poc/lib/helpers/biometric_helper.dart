import 'package:local_auth/local_auth.dart';

class BiometricHelper {
  final LocalAuthentication _localAuth = LocalAuthentication();

  Future<bool> isDeviceCapable() async {
    try {
      return await _localAuth.isDeviceSupported();
    } catch (e) {
      return false;
    }
  }

  Future<bool> isBiometricEnabled() async {
    try {
      final availableBiometrics = await _localAuth.getAvailableBiometrics();
      return availableBiometrics.isNotEmpty;
    } catch (e) {
      return false;
    }
  }

  Future<String?> getBiometricType() async {
    try {
      final availableBiometrics = await _localAuth.getAvailableBiometrics();
      if (availableBiometrics.isEmpty) return null;
      
      if (availableBiometrics.contains(BiometricType.face)) {
        return 'Face ID';
      } else if (availableBiometrics.contains(BiometricType.fingerprint)) {
        return 'Touch ID';
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  Future<bool> authenticate(String reason) async {
    try {
      return await _localAuth.authenticate(
        localizedReason: reason,
      );
    } catch (e) {
      return false;
    }
  }
}