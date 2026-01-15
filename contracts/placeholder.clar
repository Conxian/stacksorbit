;; This is a placeholder contract.
;;
;; This contract does not do anything useful.
;;

(define-data-var owner principal tx-sender)

(define-read-only (get-owner)
  (var-get owner)
)
