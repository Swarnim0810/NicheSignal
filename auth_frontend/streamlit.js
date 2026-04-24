/**
 * Streamlit Component JS Boilerplate
 */
export const Streamlit = {
  setComponentReady: function() {
    window.parent.postMessage({
      isStreamlitMessage: true,
      type: "streamlit:componentReady",
      apiVersion: 1,
    }, "*");
  },
  setFrameHeight: function(height) {
    window.parent.postMessage({
      isStreamlitMessage: true,
      type: "streamlit:setFrameHeight",
      height: height,
    }, "*");
  },
  setComponentValue: function(value) {
    window.parent.postMessage({
      isStreamlitMessage: true,
      type: "streamlit:setComponentValue",
      value: value,
    }, "*");
  },
  events: {
    addEventListener: function(type, callback) {
      window.addEventListener("message", function(event) {
        if (event.data.type === type) {
          callback(event);
        }
      });
    }
  },
  RENDER_EVENT: "streamlit:render"
};
