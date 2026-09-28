import { useState } from "react";
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { ConversationResponse } from "@northstar/validation";

import { apiBase } from "../src/config";
import type { RootStackParamList } from "../src/index";
import { ApiRequestError, askQuestion } from "../src/transport";

type Props = NativeStackScreenProps<RootStackParamList, "Conversation">;
type KpiRow = { metric_id: string; version: number; value: number | null; owner_id?: string | null };

export function ConversationScreen(_props: Props) {
  const [question, setQuestion] = useState("What is my attainment this quarter?");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [answer, setAnswer] = useState<ConversationResponse | null>(null);

  async function send(): Promise<void> {
    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      setAnswer(await askQuestion(apiBase(), question)); // Zod-validated at the boundary (ADR-026)
    } catch (err: unknown) {
      setError(err instanceof ApiRequestError ? err.message : "Something went wrong. Please retry.");
    } finally {
      setLoading(false);
    }
  }

  const kpiComponent = answer?.components.find((c) => c.type === "kpi_table");
  const kpiRows = (kpiComponent?.payload?.["rows"] ?? []) as KpiRow[];

  return (
    <View style={styles.container}>
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={question}
          onChangeText={setQuestion}
          placeholder="Ask about your pipeline…"
          autoCapitalize="none"
          multiline
        />
        <Pressable style={styles.sendButton} accessibilityLabel="Send question" onPress={() => void send()}>
          {loading ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.sendText}>Ask</Text>}
        </Pressable>
      </View>

      {error !== null && <Text style={styles.error}>{error}</Text>}

      {answer !== null && (
        <View style={styles.answerCard}>
          <Text style={styles.answer}>{answer.answer}</Text>
          <Text style={styles.asOf}>
            scope: {answer.scope.type} · as-of {answer.scope.asOf}
          </Text>
          {kpiRows.length > 0 && (
            <FlatList
              data={kpiRows}
              keyExtractor={(row) => `${row.metric_id}`}
              renderItem={({ item }) => (
                <View style={styles.kpiRow}>
                  <Text style={styles.kpiMetric}>
                    {item.metric_id} <Text style={styles.kpiVersion}>v{item.version}</Text>
                  </Text>
                  <Text style={styles.kpiValue}>{item.value === null ? "—" : item.value.toLocaleString()}</Text>
                </View>
              )}
            />
          )}
          {answer.evidence.length > 0 && (
            <Text style={styles.evidence}>
              evidence: {answer.evidence.map((e) => e.label).join(" · ")}
            </Text>
          )}
          {answer.warnings.length > 0 && <Text style={styles.warnings}>{answer.warnings.join(" · ")}</Text>}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, gap: 12, backgroundColor: "#FFFFFF" },
  inputRow: { flexDirection: "row", gap: 8 },
  input: { flex: 1, borderWidth: 1, borderColor: "#C9D2DE", borderRadius: 8, padding: 10, color: "#1A2333", minHeight: 44 },
  sendButton: { backgroundColor: "#0B5CC0", borderRadius: 8, paddingHorizontal: 18, justifyContent: "center" },
  sendText: { color: "#FFFFFF", fontWeight: "600" },
  error: { color: "#B3261E" },
  answerCard: { gap: 10, padding: 16, borderRadius: 12, backgroundColor: "#F5F7FA" },
  answer: { fontSize: 16, color: "#1A2333" },
  asOf: { fontSize: 12, color: "#4A5568" },
  kpiRow: { flexDirection: "row", justifyContent: "space-between", paddingVertical: 4 },
  kpiMetric: { color: "#1A2333" },
  kpiVersion: { color: "#4A5568", fontSize: 12 },
  kpiValue: { fontWeight: "600", color: "#1A2333" },
  evidence: { fontSize: 12, color: "#0B5CC0" },
  warnings: { fontSize: 12, color: "#8A6D00" },
});
