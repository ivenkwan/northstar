import { useEffect, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";

import { ApiRequestError, checkHealth } from "../src/transport";
import type { RootStackParamList } from "../src/index";
import { apiBase, DEFAULT_API_BASE } from "../src/config";

type Props = NativeStackScreenProps<RootStackParamList, "Home">;

export function HomeScreen({ navigation }: Props) {
  const [base, setBase] = useState(apiBase());
  const [checking, setChecking] = useState(true);
  const [healthy, setHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    setChecking(true);
    checkHealth(base)
      .then((ok) => !cancelled && setHealthy(ok))
      .catch((error: unknown) => {
        if (!cancelled && error instanceof ApiRequestError) setHealthy(false);
      })
      .finally(() => !cancelled && setChecking(false));
    return () => {
      cancelled = true;
    };
  }, [base]);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Sales Northstar</Text>
      <Text style={styles.subtitle}>Dev preview — local stack</Text>

      <View style={styles.card}>
        <Text style={styles.label}>Backend</Text>
        <TextInput
          style={styles.input}
          value={base}
          onChangeText={setBase}
          autoCapitalize="none"
          autoCorrect={false}
          placeholder={DEFAULT_API_BASE}
        />
        <Text style={styles.status}>
          {checking ? <ActivityIndicator size="small" /> : null}
          {!checking && healthy === true && <Text style={styles.ok}>● backend healthy</Text>}
          {!checking && healthy === false && (
            <Text style={styles.warn}>● unreachable — run: docker compose up -d bff metrics byok</Text>
          )}
        </Text>
      </View>

      <Pressable
        style={styles.button}
        accessibilityLabel="Open the Ask screen"
        onPress={() => navigation.navigate("Conversation", {})}
      >
        <Text style={styles.buttonText}>Ask a question</Text>
      </Pressable>

      <Text style={styles.hint}>
        Point the phone at this machine&apos;s LAN address (same Wi-Fi). Defaults to {DEFAULT_API_BASE}.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, gap: 16, backgroundColor: "#FFFFFF" },
  title: { fontSize: 28, fontWeight: "700", color: "#1A2333" },
  subtitle: { fontSize: 14, color: "#4A5568" },
  card: { padding: 16, borderRadius: 12, backgroundColor: "#F5F7FA", gap: 8 },
  label: { fontSize: 12, color: "#4A5568", textTransform: "uppercase" },
  input: { borderWidth: 1, borderColor: "#C9D2DE", borderRadius: 8, padding: 10, color: "#1A2333" },
  status: { minHeight: 20 },
  ok: { color: "#1E6B3A" },
  warn: { color: "#B3261E" },
  button: { backgroundColor: "#0B5CC0", borderRadius: 10, paddingVertical: 14, alignItems: "center" },
  buttonText: { color: "#FFFFFF", fontSize: 16, fontWeight: "600" },
  hint: { fontSize: 12, color: "#4A5568" },
});
