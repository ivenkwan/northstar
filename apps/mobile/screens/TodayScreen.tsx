import { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { Briefing } from "@northstar/validation";

import { apiBase } from "../src/config";
import type { RootStackParamList } from "../src/index";
import { ApiRequestError, getTodayBriefing } from "../src/transport";

type Props = NativeStackScreenProps<RootStackParamList, "Today">;

/** §10.2 interaction rules: concise card first, details and evidence on demand;
 * risk dots always paired with text labels (no color-only encoding, ADR-036). */
export function TodayScreen({ navigation }: Props) {
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setBriefing(await getTodayBriefing(apiBase())); // Zod-validated (ADR-026)
    } catch (err: unknown) {
      setError(err instanceof ApiRequestError ? err.message : "Something went wrong. Please retry.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return (
      <View style={[styles.container, styles.center]}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {error !== null && (
        <View style={styles.errorCard}>
          <Text style={styles.errorText}>{error}</Text>
          <Pressable accessibilityLabel="Retry loading briefing" onPress={() => void load()}>
            <Text style={styles.retry}>Retry</Text>
          </Pressable>
        </View>
      )}
      {briefing !== null && (
        <FlatList
          data={[0]}
          keyExtractor={(i) => String(i)}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => void load()} />}
          renderItem={() => (
            <View style={styles.content}>
              <Text style={styles.greeting}>{briefing.greeting}</Text>
              <Text style={styles.asOf}>data as-of {briefing.asOf}</Text>

              <View style={styles.kpiRow}>
                {briefing.kpis.slice(0, 3).map((kpi) => (
                  <View key={kpi.metricId} style={styles.kpiCard}>
                    <Text style={styles.kpiLabel}>{kpi.metricId}</Text>
                    <Text style={styles.kpiValue}>
                      {kpi.value === null ? "—" : kpi.value.toLocaleString()}
                    </Text>
                  </View>
                ))}
              </View>

              <Text style={styles.section}>Top risks</Text>
              {briefing.topRisks.map((risk) => (
                <View key={risk.opportunityId} style={styles.riskCard}>
                  <Text style={styles.riskTitle}>
                    <Text style={risk.topSeverity === "critical" ? styles.critical : styles.warning}>
                      {risk.topSeverity === "critical" ? "● critical" : risk.topSeverity === "warning" ? "● warning" : "● healthy"}
                    </Text>
                    {"  "}
                    {risk.headline}
                  </Text>
                  {risk.nextSteps[0] !== undefined && <Text style={styles.nextStep}>→ {risk.nextSteps[0]}</Text>}
                </View>
              ))}
              {briefing.topRisks.length === 0 && <Text style={styles.empty}>No open risks — clean pipeline.</Text>}

              <Text style={styles.section}>Market signals</Text>
              {briefing.marketSignals.map((signal) => (
                <View key={`${signal.entity}-${signal.signalType}`} style={styles.signalCard}>
                  <Text style={styles.signalHeadline}>{signal.headline}</Text>
                  <Text style={styles.signalMeta}>
                    {signal.signalType} · {signal.entity} · {signal.source} · confidence{" "}
                    {(signal.confidence * 100).toFixed(0)}%
                  </Text>
                </View>
              ))}

              {briefing.overdueActions > 0 && (
                <Text style={styles.overdue}>Overdue actions: {briefing.overdueActions}</Text>
              )}

              <Pressable
                style={styles.askButton}
                accessibilityLabel="Open the Ask screen"
                onPress={() => navigation.navigate("Conversation", {})}
              >
                <Text style={styles.askButtonText}>Ask a question</Text>
              </Pressable>
            </View>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#FFFFFF" },
  center: { alignItems: "center", justifyContent: "center" },
  content: { padding: 20, gap: 10 },
  greeting: { fontSize: 22, fontWeight: "700", color: "#1A2333" },
  asOf: { fontSize: 12, color: "#4A5568" },
  kpiRow: { flexDirection: "row", gap: 8, marginTop: 6 },
  kpiCard: { flex: 1, padding: 12, borderRadius: 10, backgroundColor: "#F5F7FA" },
  kpiLabel: { fontSize: 11, color: "#4A5568", textTransform: "uppercase" },
  kpiValue: { fontSize: 18, fontWeight: "700", color: "#1A2333" },
  section: { fontSize: 14, fontWeight: "600", color: "#1A2333", marginTop: 12 },
  riskCard: { padding: 12, borderRadius: 10, backgroundColor: "#F5F7FA", gap: 4 },
  riskTitle: { color: "#1A2333", fontSize: 14 },
  critical: { color: "#B3261E", fontWeight: "700" },
  warning: { color: "#8A6D00", fontWeight: "700" },
  nextStep: { fontSize: 12, color: "#0B5CC0" },
  empty: { color: "#4A5568" },
  signalCard: { padding: 12, borderRadius: 10, borderWidth: 1, borderColor: "#C9D2DE", gap: 4 },
  signalHeadline: { color: "#1A2333", fontSize: 14 },
  signalMeta: { fontSize: 11, color: "#4A5568" },
  overdue: { color: "#8A6D00", fontSize: 12, marginTop: 8 },
  askButton: { marginTop: 16, backgroundColor: "#0B5CC0", borderRadius: 10, paddingVertical: 14, alignItems: "center" },
  askButtonText: { color: "#FFFFFF", fontSize: 16, fontWeight: "600" },
  errorCard: { margin: 20, padding: 16, borderRadius: 12, backgroundColor: "#F5F7FA", gap: 8 },
  errorText: { color: "#B3261E" },
  retry: { color: "#0B5CC0", fontWeight: "600" },
});
