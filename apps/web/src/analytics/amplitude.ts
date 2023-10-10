export * as amplitude from "@amplitude/analytics-browser";
import * as amplitude from "@amplitude/analytics-browser";

export const trackClickLink = (url: string) => {
  amplitude.track("Click Link", { url });
};

export const trackSave = () => {
  amplitude.track("Save");
};

export const trackAddPage = () => {
  amplitude.track("Add Page");
};

export const trackSend = () => {
  amplitude.track("Send");
};
