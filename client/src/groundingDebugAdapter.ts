import { execFile } from "child_process";
import * as path from "path";
import { promisify } from "util";
import {
  DebugSession,
  InitializedEvent,
  OutputEvent,
  StoppedEvent,
  TerminatedEvent,
  Thread,
} from "@vscode/debugadapter";
import { DebugProtocol } from "@vscode/debugprotocol";
import {
  advanceStepIndex,
  frameAt,
  isSessionFinished,
  parseGroundingDebugPayload,
  type GroundingStep,
  variableEntries,
} from "./groundingDebugCore";

const execFileAsync = promisify(execFile);

export type GroundingDebugLaunchArgs = DebugProtocol.LaunchRequestArguments & {
  program: string;
  pythonPath: string;
  scriptPath: string;
};

export class GroundingDebugSession extends DebugSession {
  private steps: GroundingStep[] = [];
  private stepIndex = -1;

  protected initializeRequest(response: DebugProtocol.Response): void {
    response.body = response.body ?? {};
    response.body.supportsConfigurationDoneRequest = true;
    this.sendResponse(response);
    this.sendEvent(new InitializedEvent());
  }

  protected launchRequest(
    response: DebugProtocol.LaunchResponse,
    args: DebugProtocol.LaunchRequestArguments,
  ): void {
    void this.runLaunch(response, args as GroundingDebugLaunchArgs);
  }

  private async runLaunch(
    response: DebugProtocol.LaunchResponse,
    args: GroundingDebugLaunchArgs,
  ): Promise<void> {
    try {
      this.steps = await loadGroundingSteps(args);
      this.stepIndex = this.steps.length > 0 ? 0 : -1;
      this.sendResponse(response);
      if (isSessionFinished(this.stepIndex, this.steps.length)) {
        this.sendEvent(new TerminatedEvent());
        return;
      }
      this.stopAtNextStep("launch");
    } catch (err) {
      this.sendEvent(new OutputEvent(`${String(err)}\n`, "stderr"));
      this.sendResponse(response);
      this.sendEvent(new TerminatedEvent());
    }
  }

  protected configurationDoneRequest(response: DebugProtocol.Response): void {
    this.sendResponse(response);
  }

  protected threadsRequest(response: DebugProtocol.Response): void {
    response.body = { threads: [new Thread(1, "grounding")] };
    this.sendResponse(response);
  }

  protected stackTraceRequest(
    response: DebugProtocol.Response,
    _args: DebugProtocol.StackTraceArguments,
  ): void {
    const frame = frameAt(this.steps, this.stepIndex);
    response.body = {
      stackFrames: [
        {
          id: 1,
          name: frame
            ? `step ${frame.stepIndex + 1}/${this.steps.length}: ${frame.step.kind}`
            : "grounding",
          line: 1,
          column: 1,
          source: { name: "grounding trace", path: "<grounding>" },
        },
      ],
      totalFrames: 1,
    };
    this.sendResponse(response);
  }

  protected scopesRequest(
    response: DebugProtocol.Response,
    _args: DebugProtocol.ScopesArguments,
  ): void {
    response.body = {
      scopes: [
        {
          name: "Grounding",
          variablesReference: 1,
          expensive: false,
        },
      ],
    };
    this.sendResponse(response);
  }

  protected variablesRequest(
    response: DebugProtocol.Response,
    _args: DebugProtocol.VariablesArguments,
  ): void {
    const frame = frameAt(this.steps, this.stepIndex);
    response.body = {
      variables: variableEntries(frame?.step).map((entry, index) => ({
        name: entry.name,
        value: entry.value,
        variablesReference: 0,
        indexedVariables: index,
      })),
    };
    this.sendResponse(response);
  }

  protected continueRequest(
    response: DebugProtocol.Response,
    _args: DebugProtocol.ContinueArguments,
  ): void {
    this.stepIndex = advanceStepIndex(this.steps, this.stepIndex, "continue");
    this.sendResponse(response);
    if (isSessionFinished(this.stepIndex, this.steps.length)) {
      this.sendEvent(new TerminatedEvent());
      return;
    }
    this.stopAtNextStep("continue");
  }

  protected nextRequest(
    response: DebugProtocol.Response,
    _args: DebugProtocol.NextArguments,
  ): void {
    this.stepIndex = advanceStepIndex(this.steps, this.stepIndex, "next");
    this.sendResponse(response);
    if (isSessionFinished(this.stepIndex, this.steps.length)) {
      this.sendEvent(new TerminatedEvent());
      return;
    }
    this.stopAtNextStep("step");
  }

  protected disconnectRequest(
    response: DebugProtocol.Response,
    _args: DebugProtocol.DisconnectArguments,
  ): void {
    this.sendResponse(response);
  }

  private stopAtNextStep(reason: string): void {
    this.sendEvent(new StoppedEvent(reason, 1));
  }
}

export async function loadGroundingSteps(
  args: GroundingDebugLaunchArgs,
): Promise<GroundingStep[]> {
  const { stdout, stderr } = await execFileAsync(
    args.pythonPath,
    [args.scriptPath, args.program],
    { maxBuffer: 10 * 1024 * 1024 },
  );
  if (stderr.trim()) {
    throw new Error(stderr.trim());
  }
  const payload = parseGroundingDebugPayload(stdout.trim());
  return payload.steps;
}

export function resolveGroundingDebugScript(extensionPath: string): string {
  return path.join(extensionPath, "server", "grounding_debug.py");
}
