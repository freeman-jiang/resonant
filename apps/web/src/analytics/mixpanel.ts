import { CreateUserRequest } from "@/api";
import mixpanel from "mixpanel-browser";

export const trackSearch = (query: string) => {
  mixpanel.track("Search", { query });
};

export const trackClickOutboundLink = (url: string) => {
  mixpanel.track("Click Outbound Link", { url });
};

export const trackSave = () => {
  mixpanel.track("Save");
};

export const trackBroadcast = () => {
  mixpanel.track("Broadcast");
};

export const trackOnboard = (body: CreateUserRequest) => {
  mixpanel.track("Onboard", body);
};

export const trackAddPage = () => {
  mixpanel.track("Add Page");
};

export const trackSend = () => {
  mixpanel.track("Send");
};

export const trackSignIn = () => {
  mixpanel.track("Sign In");
};

export const trackClickPage = (url: string) => {
  mixpanel.track("Click Page", { url });
};

export const trackClickLinkedBy = (pageUrl: string, linkedByUrl: string) => {
  mixpanel.track("Click Linked By", { pageUrl, linkedByUrl });
};

export const trackClickTopic = (topic: string) => {
  mixpanel.track("Click Topic", { topic });
};

export const trackComment = ({
  pageUrl,
  comment,
}: {
  pageUrl: string;
  comment: string;
}) => {
  mixpanel.track("Comment", { pageUrl, comment });
};
