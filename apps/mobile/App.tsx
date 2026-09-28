import { NavigationContainer, type LinkingOptions } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { StatusBar } from "expo-status-bar";

import { ConversationScreen } from "./screens/ConversationScreen";
import { HomeScreen } from "./screens/HomeScreen";
import { TodayScreen } from "./screens/TodayScreen";
import type { RootStackParamList } from "./src/index";

const Stack = createNativeStackNavigator<RootStackParamList>();

// northstar:// links: only the screens mapped here resolve; unknown paths match
// nothing and never navigate (fail-safe). Domain-layer link validation is
// exercised at the navigation boundary in the full shell (§17.7, tested in
// packages/validation + apps/mobile domain tests).
const linking: LinkingOptions<RootStackParamList> = {
  prefixes: ["northstar://"],
  config: {
    screens: {
      Home: "Home",
      Conversation: "Conversation",
      Pipeline: "Pipeline",
      Account: "Account",
      Intelligence: "Intelligence",
      Dashboard: "Dashboard",
      Today: "Today",
    },
  },
};

export default function App() {
  return (
    <>
      <StatusBar style="dark" />
      <NavigationContainer linking={linking}>
        <Stack.Navigator initialRouteName="Today">
          <Stack.Screen name="Today" component={TodayScreen} options={{ title: "Today" }} />
          <Stack.Screen name="Conversation" component={ConversationScreen} options={{ title: "Ask" }} />
          <Stack.Screen name="Home" component={HomeScreen} options={{ title: "Settings" }} />
        </Stack.Navigator>
      </NavigationContainer>
    </>
  );
}
