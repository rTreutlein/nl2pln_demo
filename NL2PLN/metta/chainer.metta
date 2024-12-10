;; Define Nat
(: Nat Type)
(: Z Nat)
(: S (-> Nat Nat))

;; Define <=
(: <= (-> $a $a Bool))
(= (<= $x $y) (or (< $x $y) (== $x $y)))

;; Define cast functions between Nat and Number
(: fromNumber (-> Number Nat))
(= (fromNumber $n) (if (<= $n 0) Z (S (fromNumber (- $n 1)))))
(: fromNat (-> Nat Number))
(= (fromNat Z) 0)
(= (fromNat (S $k)) (+ 1 (fromNat $k)))

;;;;;;;;;;;;;;;;;;;;;;
;; Backward chainer ;;
;;;;;;;;;;;;;;;;;;;;;;
(: bc (-> $a                            ; Knowledge base space
          Nat                           ; Maximum depth
          $q                            ; Query
          $r))                          ; Result

;; Base cases

;; Match the knowledge base
(= (bc $kb $_ (: $prf $thrm))
   (match $kb (: $prf $thrm) (: $prf $thrm)))

; Recursive steps
(= (bc $kb (S $k) (: ($prfabs $prfarg) $thrm))
   (let* (((: $prfabs (-> (: $prfarg $prms) $thrm))
           (bc $kb $k (: $prfabs (-> (: $prfarg $prms) $thrm))))
          ((: $prfarg $prms)
           (bc $kb $k (: $prfarg $prms))))
     (: ($prfabs $prfarg) $thrm)))

;; Define ad-atom-nodup, that adds an atom only if it is not already
;; in the atomspace
(: add-atom-nodup (-> $st Atom ()))
(= (add-atom-nodup $space $atom)
   (case (match $space $atom $atom)
     (($atom (Empty))
      (Empty (add-atom $space $atom)))))

(= (fc $kb (: $prf $_))
    (let* (($out (bc $kb (S (S Z)) (: ($prfabs $prf) $thrm)))
           ($dummy (add-atom-nodup $kb $out))
          )
    $out
))

;;deduplicatig bc
(= (ddbc $kb $query)
    (let* (($out (bc $kb (S (S Z)) $query))
           ($dummy (add-atom-nodup $kb $out))
          )
    $out
))
