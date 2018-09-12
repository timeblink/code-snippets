(ns cherrypick.core
  (:require 
    [clojure.string :as str]
    [clojure.tools.logging :as log]
    [clj-http.client :as client])
  (:use 
    [clojure.tools.cli :only [cli]]
    [slingshot.slingshot :only [throw+ try+]])
  (:gen-class))

(defn try_post_uri [uri,cookie,data]
  (println uri)
  (try+
    (client/post uri 
      { :headers {"content-type" "application/json"}
        :cookie-store cookie})
    (catch [:status 403] {:keys [request-time headers body]}
      (log/warn "403" request-time headers))
    (catch [:status 404] {:keys [request-time headers body]}
      (log/warn "NOT Found 404" request-time headers body))
    (catch Object _
      (log/error (:throwable &throw-context) "unexpected error")
      (throw+))))

(defn application [opts]
  (let
    [ change_uri (str/join "/" [(opts :gerrit) "a" "changes" (opts :changeid)])
      revision_uri (str/join "/" [change_uri "revisions" (opts :revision)])
      login_uri (str/join "/" [(opts :gerrit) "login"])
      commit_uri (str/join "/" [revision_uri "commit"])
      topic_uri (str/join "/" [change_uri "topic"])
      my-cs (clj-http.cookies/cookie-store)]
    (println login_uri)
    (client/post login_uri
      { :form-params {:username (opts :username) :password (opts :password)} 
        :cookie-store my-cs})
    (try_post_uri 
      (str/join "/" [change_uri "abandon"]) my-cs {})
  ))

(defn -main [& args]
  (let [
    [options args banner] (cli args
      ["--gerrit" "gerrit" :default "http://127.0.0.1:8080/gerrit"]
      ["--changeid" "changeid" :default "Ixxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"]
      ["--revision" "revision" :default "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"]
      ["--username" "username" :default "username"]
      ["--password" "password" :default "password"]
      ["--[no-]debug" "debug mode" :default true]
      ["--[no-]verbose" "verbose mode" :default false]
      ["--help" "show help" :default false :flag true])]
    (when (:help options) (println banner) (System/exit 0))
    (application options)))
